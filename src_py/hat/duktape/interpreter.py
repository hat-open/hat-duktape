import collections
import sys
import typing

from hat.duktape import lib


Data: typing.TypeAlias = (None | bool | int | float | str |
                          typing.List['Data'] |
                          typing.Dict[str, 'Data'] |
                          typing.Callable)
"""Supported data types"""


class EvalError(Exception):
    """Evaluation error"""


class Interpreter:
    """JavaScript interpreter

    High-level python wrapper for duktape JavaScript interpreter.

    Current implementation caches all function objects for preventing
    garbage collection.

    """

    def __init__(self, lib: lib.Lib = lib.default_lib):
        self._lib = lib
        self._ctx = None
        self._fns = collections.deque()

        @self._lib.duk_fatal_function
        def fatal_handler(udata, msg):
            try:
                print(f"duktape fatal error: {msg.decode('utf-8')}",
                      file=sys.stderr, flush=True)

            finally:
                sys.exit(1)

        self._ctx = lib.duk_create_heap(None, None, None, None, fatal_handler)
        self._fns.append(fatal_handler)

    def __del__(self):
        if self._ctx is not None:
            self._lib.duk_destroy_heap(self._ctx)

        self._fns.clear()

    def eval(self,
             code: str,
             with_result: bool = True
             ) -> Data:
        """Evaluate JS code and optionally return last expression"""
        top = self._lib.duk_get_top(self._ctx)

        try:
            if self._lib.duk_peval_string(self._ctx, code.encode('utf-8')):
                stacktrace_bytes = self._lib.duk_safe_to_stacktrace(self._ctx,
                                                                    -1)
                raise EvalError(stacktrace_bytes.decode('utf-8'))

            if with_result:
                return self._peek(-1)

        finally:
            self._lib.duk_set_top(self._ctx, top)

    def get(self, name: str) -> Data:
        """Get global value"""
        top = self._lib.duk_get_top(self._ctx)

        try:
            key = name.encode('utf-8')
            self._lib.duk_get_global_string(self._ctx, key)
            return self._peek(-1)

        finally:
            self._lib.duk_set_top(self._ctx, top)

    def set(self, name: str, value: Data):
        """Set global value"""
        top = self._lib.duk_get_top(self._ctx)

        try:
            self._push(value)
            key = name.encode('utf-8')
            self._lib.duk_put_global_string(self._ctx, key)

        finally:
            self._lib.duk_set_top(self._ctx, top)

    def _peek(self, idx):
        if self._lib.duk_is_null_or_undefined(self._ctx, idx):
            return

        if self._lib.duk_is_boolean(self._ctx, idx):
            return self._peek_boolean(idx)

        if self._lib.duk_is_number(self._ctx, idx):
            return self._peek_number(idx)

        if self._lib.duk_is_string(self._ctx, idx):
            return self._peek_string(idx)

        if self._lib.duk_is_array(self._ctx, idx):
            return self._peek_array(idx)

        if self._lib.duk_is_function(self._ctx, idx):
            return self._peek_function(idx)

        if self._lib.duk_is_object(self._ctx, idx):
            return self._peek_object(idx)

        raise ValueError()

    def _peek_boolean(self, idx):
        return bool(self._lib.duk_get_boolean(self._ctx, idx))

    def _peek_number(self, idx):
        return self._lib.duk_get_number(self._ctx, idx)

    def _peek_string(self, idx):
        return self._lib.duk_get_string(self._ctx, idx).decode('utf-8')

    def _peek_array(self, idx):
        result = []
        top = self._lib.duk_get_top(self._ctx)
        self._lib.duk_enum(self._ctx, idx,
                           self._lib.DUK_ENUM_ARRAY_INDICES_ONLY)

        try:
            while self._lib.duk_next(self._ctx, top, 1):
                result.append(self._peek(-1))

        finally:
            self._lib.duk_set_top(self._ctx, top)

        return result

    def _peek_object(self, idx):
        result = {}
        top = self._lib.duk_get_top(self._ctx)
        self._lib.duk_enum(self._ctx, idx,
                           self._lib.DUK_ENUM_OWN_PROPERTIES_ONLY)

        try:
            while self._lib.duk_next(self._ctx, top, 1):
                key = self._peek(-2)
                value = self._peek(-1)
                result[key] = value

        finally:
            self._lib.duk_set_top(self._ctx, top)

        return result

    def _peek_function(self, idx):
        fn_ptr = self._lib.duk_get_heapptr(self._ctx, idx)
        self._stash(fn_ptr)

        def wrapper(*args):
            top = self._lib.duk_push_heapptr(self._ctx, fn_ptr)

            try:
                for arg in args:
                    self._push(arg)
                self._lib.duk_call(self._ctx, len(args))
                return self._peek(-1)

            finally:
                self._lib.duk_set_top(self._ctx, top)

        return wrapper

    def _push(self, value):
        if value is None:
            self._push_null()

        elif isinstance(value, bool):
            self._push_boolean(value)

        elif isinstance(value, int) or isinstance(value, float):
            self._push_number(value)

        elif isinstance(value, str):
            self._push_string(value)

        elif isinstance(value, list) or isinstance(value, tuple):
            self._push_array(value)

        elif isinstance(value, dict):
            self._push_object(value)

        elif callable(value):
            self._push_function(value)

        else:
            raise ValueError()

    def _push_null(self):
        self._lib.duk_push_null(self._ctx)

    def _push_boolean(self, value):
        self._lib.duk_push_boolean(self._ctx, value)

    def _push_number(self, value):
        self._lib.duk_push_number(self._ctx, value)

    def _push_string(self, value):
        self._lib.duk_push_string(self._ctx, value.encode('utf-8'))

    def _push_array(self, value):
        arr_idx = self._lib.duk_push_array(self._ctx)

        try:
            for index, element in enumerate(value):
                self._push(element)
                if self._lib.duk_put_prop_index(self._ctx, arr_idx,
                                                index) != 1:
                    raise Exception('could not add element to array')

        except Exception:
            self._lib.duk_set_top(self._ctx, arr_idx)
            raise

    def _push_object(self, value):
        obj_idx = self._lib.duk_push_object(self._ctx)

        try:
            for k, v in value.items():
                self._push(v)
                if self._lib.duk_put_prop_string(self._ctx, obj_idx,
                                                 k.encode('utf-8')) != 1:
                    raise Exception('could not add property to object')

        except Exception:
            self._lib.duk_set_top(self._ctx, obj_idx)
            raise

    def _push_function(self, value):

        @self._lib.duk_c_function
        def wrapper(ctx):
            args = []
            args_count = self._lib.duk_get_top(self._ctx)

            try:
                for i in range(args_count):
                    args.append(self._peek(i))
                result = value(*args)
                self._push(result)

            except Exception:
                return self._lib.DUK_RET_ERROR

            return 1

        self._lib.duk_push_c_function(self._ctx, wrapper,
                                      self._lib.DUK_VARARGS)
        self._fns.append(wrapper)

    def _stash(self, ptr):
        top = self._lib.duk_get_top(self._ctx)

        try:
            ptr_id = int(ptr)
            self._lib.duk_push_heap_stash(self._ctx)
            self._lib.duk_push_heapptr(self._ctx, ptr)
            if self._lib.duk_put_prop_index(self._ctx, -2, ptr_id) != 1:
                raise Exception("couldn't stash pointer")

        finally:
            self._lib.duk_set_top(self._ctx, top)
