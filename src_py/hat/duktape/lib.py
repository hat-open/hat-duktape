import contextlib
import ctypes
import importlib.resources
import pathlib
import sys


class Lib:
    """Duktape library

    Low-level python ctypes wrapper for duktape JavaScript library.

    If `path` to dynamic library is not set, builtin dynamic library is used.

    """

    def __init__(self, path: pathlib.Path | None = None):
        self._ctx = contextlib.ExitStack()

        lib = self._load_lib(path)

        self._init_functions(lib)
        self._init_constants(lib)

    def __del__(self):
        self._ctx.close()

    def _load_lib(self, path):
        if path is None:
            if sys.platform == 'win32':
                _lib_suffix = '.dll'

            elif sys.platform == 'darwin':
                _lib_suffix = '.dylib'

            else:
                _lib_suffix = '.so'

            path = self._ctx.enter_context(
                importlib.resources.as_file(
                    importlib.resources.files(__package__) /
                    f'duktape{_lib_suffix}'))

        return ctypes.cdll.LoadLibrary(str(path))

    def _init_functions(self, lib):
        duk_size_t = ctypes.c_size_t
        duk_int_t = ctypes.c_int
        duk_uint_t = ctypes.c_uint
        duk_small_int_t = ctypes.c_int
        duk_small_uint_t = ctypes.c_uint
        duk_bool_t = duk_small_uint_t
        duk_idx_t = duk_int_t
        duk_uarridx_t = duk_uint_t
        duk_ret_t = duk_small_int_t
        duk_double_t = ctypes.c_double
        duk_context_p = ctypes.c_void_p

        self.duk_c_function = ctypes.CFUNCTYPE(duk_ret_t,
                                               duk_context_p)
        self.duk_fatal_function = ctypes.CFUNCTYPE(None,
                                                   ctypes.c_void_p,
                                                   ctypes.c_char_p)

        functions = [
            (None, 'duk_call', [duk_context_p,
                                duk_idx_t]),
            (duk_context_p, 'duk_create_heap', [ctypes.c_void_p,
                                                ctypes.c_void_p,
                                                ctypes.c_void_p,
                                                ctypes.c_void_p,
                                                self.duk_fatal_function]),
            (None, 'duk_destroy_heap', [duk_context_p]),
            (None, 'duk_enum', [duk_context_p,
                                duk_idx_t,
                                duk_uint_t]),
            (duk_int_t, 'duk_eval_raw', [duk_context_p,
                                         ctypes.c_char_p,
                                         duk_size_t,
                                         duk_uint_t]),
            (duk_bool_t, 'duk_get_boolean', [duk_context_p,
                                             duk_idx_t]),
            (duk_bool_t, 'duk_get_global_string', [duk_context_p,
                                                   ctypes.c_char_p]),
            (ctypes.c_void_p, 'duk_get_heapptr', [duk_context_p,
                                                  duk_idx_t]),
            (duk_double_t, 'duk_get_number', [duk_context_p,
                                              duk_idx_t]),
            (ctypes.c_char_p, 'duk_get_string', [duk_context_p,
                                                 duk_idx_t]),
            (duk_idx_t, 'duk_get_top', [duk_context_p]),
            (duk_uint_t, 'duk_get_type_mask', [duk_context_p,
                                               duk_idx_t]),
            (duk_bool_t, 'duk_is_array', [duk_context_p,
                                          duk_idx_t]),
            (duk_bool_t, 'duk_is_boolean', [duk_context_p,
                                            duk_idx_t]),
            (duk_bool_t, 'duk_is_function', [duk_context_p,
                                             duk_idx_t]),
            (duk_bool_t, 'duk_is_number', [duk_context_p,
                                           duk_idx_t]),
            (duk_bool_t, 'duk_is_object', [duk_context_p,
                                           duk_idx_t]),
            (duk_bool_t, 'duk_is_string', [duk_context_p,
                                           duk_idx_t]),
            (duk_bool_t, 'duk_next', [duk_context_p,
                                      duk_idx_t,
                                      duk_bool_t]),
            (duk_idx_t, 'duk_push_array', [duk_context_p]),
            (None, 'duk_push_boolean', [duk_context_p,
                                        duk_bool_t]),
            (duk_idx_t, 'duk_push_c_function', [duk_context_p,
                                                self.duk_c_function,
                                                duk_idx_t]),
            (duk_idx_t, 'duk_push_heapptr', [duk_context_p,
                                             ctypes.c_void_p]),
            (None, 'duk_push_heap_stash', [duk_context_p]),
            (None, 'duk_push_null', [duk_context_p]),
            (None, 'duk_push_number', [duk_context_p,
                                       duk_double_t]),
            (duk_idx_t, 'duk_push_object', [duk_context_p]),
            (ctypes.c_char_p, 'duk_push_string', [duk_context_p,
                                                  ctypes.c_char_p]),
            (duk_bool_t, 'duk_put_global_string', [duk_context_p,
                                                   ctypes.c_char_p]),
            (duk_bool_t, 'duk_put_prop_index', [duk_context_p,
                                                duk_idx_t,
                                                duk_uarridx_t]),
            (duk_bool_t, 'duk_put_prop_string', [duk_context_p,
                                                 duk_idx_t,
                                                 ctypes.c_char_p]),
            (ctypes.c_char_p, 'duk_safe_to_stacktrace', [duk_context_p,
                                                         duk_idx_t]),
            (None, 'duk_set_top', [duk_context_p,
                                   duk_idx_t])
        ]

        for restype, name, argtypes in functions:
            function = getattr(lib, name)
            function.argtypes = argtypes
            function.restype = restype
            setattr(self, name, function)

    def _init_constants(self, lib):
        DUK_ERR_ERROR = 1
        DUK_COMPILE_EVAL = (1 << 3)
        DUK_COMPILE_SAFE = (1 << 7)
        DUK_COMPILE_NOSOURCE = (1 << 9)
        DUK_COMPILE_STRLEN = (1 << 10)
        DUK_COMPILE_NOFILENAME = (1 << 11)
        DUK_TYPE_MASK_UNDEFINED = (1 << 1)
        DUK_TYPE_MASK_NULL = (1 << 2)

        self.DUK_ENUM_OWN_PROPERTIES_ONLY = (1 << 4)
        self.DUK_ENUM_ARRAY_INDICES_ONLY = (1 << 5)
        self.DUK_VARARGS = -1
        self.DUK_RET_ERROR = - DUK_ERR_ERROR

        self.duk_peval_string = lambda ctx, src: lib.duk_eval_raw(
            ctx, src, 0,
            0 | DUK_COMPILE_EVAL | DUK_COMPILE_SAFE | DUK_COMPILE_NOSOURCE |
            DUK_COMPILE_STRLEN | DUK_COMPILE_NOFILENAME)

        self.duk_is_null_or_undefined = lambda ctx, idx: bool(
            lib.duk_get_type_mask(ctx, idx) &
            (DUK_TYPE_MASK_NULL | DUK_TYPE_MASK_UNDEFINED))


default_lib: Lib = Lib()
