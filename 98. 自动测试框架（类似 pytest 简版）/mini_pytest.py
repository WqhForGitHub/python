"""
自动测试框架（类似 pytest 简版）- 纯 Python 实现
=====================================
特性：
- 自动发现 test_*.py / Test* 类 / test_* 函数
- 支持 setup/teardown 钩子
- 断言通过函数 assert_eq, assert_true 等（也兼容原生 assert）
- 参数化测试（@parametrize）
- 测试报告（颜色终端输出 + 摘要）
- fixtures 装饰器（简化版）

使用：
    python mini_pytest.py [path]
"""

import importlib.util
import inspect
import os
import sys
import time
import traceback
import re


# ---------- 断言工具 ----------
class AssertionFail(AssertionError):
    pass


def assert_eq(actual, expected, msg=None):
    if actual != expected:
        raise AssertionFail(msg or f"expected {expected!r}, got {actual!r}")


def assert_true(cond, msg=None):
    if not cond:
        raise AssertionFail(msg or f"expected truthy, got {cond!r}")


def assert_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    except Exception as e:
        raise AssertionFail(f"expected {exc_type.__name__}, got {type(e).__name__}")
    raise AssertionFail(f"expected {exc_type.__name__}, no exception raised")


# ---------- 装饰器 ----------
def parametrize(arg_names, arg_values):
    """简化版 @parametrize("x,y,expected", [(1,2,3),(2,3,5)])"""
    names = [n.strip() for n in arg_names.split(",")]

    def deco(fn):
        fn._parametrize = (names, arg_values)
        return fn

    return deco


_FIXTURES = {}


def fixture(fn):
    _FIXTURES[fn.__name__] = fn
    return fn


def skip(reason="skipped"):
    def deco(fn):
        fn._skip = reason
        return fn

    return deco


# ---------- 测试用例 ----------
class TestCase:
    def __init__(self, name, fn, args=None, instance=None, setup=None, teardown=None):
        self.name = name
        self.fn = fn
        self.args = args or {}
        self.instance = instance
        self.setup = setup
        self.teardown = teardown


class Result:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.skipped = False
        self.skip_reason = None
        self.error = None
        self.duration = 0.0


# ---------- 收集器 ----------
class Collector:
    def __init__(self):
        self.cases = []

    def collect_module(self, mod):
        for name, obj in inspect.getmembers(mod):
            if inspect.isfunction(obj) and name.startswith("test_"):
                self._add_function(obj, name)
            elif inspect.isclass(obj) and name.startswith("Test"):
                self._add_class(obj, name)

    def _add_function(self, fn, name, prefix=""):
        full_name = prefix + name
        if hasattr(fn, "_parametrize"):
            arg_names, arg_values = fn._parametrize
            for vals in arg_values:
                args = dict(zip(arg_names, vals))
                case_name = f"{full_name}[{','.join(map(repr, vals))}]"
                self.cases.append(TestCase(case_name, fn, args))
        else:
            self.cases.append(TestCase(full_name, fn))

    def _add_class(self, cls, cls_name):
        instance = cls()
        setup = getattr(instance, "setup", None) or getattr(instance, "setup_method", None)
        teardown = getattr(instance, "teardown", None) or getattr(instance, "teardown_method", None)
        for mname, method in inspect.getmembers(instance, inspect.ismethod):
            if mname.startswith("test_"):
                full = f"{cls_name}.{mname}"
                if hasattr(method.__func__, "_parametrize"):
                    arg_names, arg_values = method.__func__._parametrize
                    for vals in arg_values:
                        args = dict(zip(arg_names, vals))
                        case_name = f"{full}[{','.join(map(repr, vals))}]"
                        self.cases.append(TestCase(case_name, method, args, instance, setup, teardown))
                else:
                    self.cases.append(TestCase(full, method, {}, instance, setup, teardown))


# ---------- 运行器 ----------
class Runner:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = []

    def run(self, cases):
        start = time.time()
        for case in cases:
            r = self._run_one(case)
            self.results.append(r)
            self._print_result(r)
        elapsed = time.time() - start
        self._summary(elapsed)
        return all(r.passed or r.skipped for r in self.results)

    def _run_one(self, case):
        r = Result(case.name)
        if hasattr(case.fn, "_skip"):
            r.skipped = True
            r.skip_reason = case.fn._skip
            return r

        t0 = time.time()
        try:
            if case.setup:
                case.setup()
            # 注入 fixtures
            sig = inspect.signature(case.fn)
            kwargs = dict(case.args)
            for pname in sig.parameters:
                if pname == "self":
                    continue
                if pname in kwargs:
                    continue
                if pname in _FIXTURES:
                    kwargs[pname] = _FIXTURES[pname]()
            case.fn(**kwargs)
            r.passed = True
        except AssertionFail as e:
            r.error = ("ASSERT", str(e), traceback.format_exc())
        except Exception as e:
            r.error = ("ERROR", f"{type(e).__name__}: {e}", traceback.format_exc())
        finally:
            try:
                if case.teardown:
                    case.teardown()
            except Exception:
                pass
            r.duration = time.time() - t0
        return r

    def _print_result(self, r):
        if r.skipped:
            mark, color = "S", "\033[33m"
        elif r.passed:
            mark, color = ".", "\033[32m"
        else:
            mark, color = "F", "\033[31m"
        if self.verbose:
            status = "PASS" if r.passed else ("SKIP" if r.skipped else "FAIL")
            print(f"  {color}[{status}]\033[0m {r.name} ({r.duration*1000:.1f}ms)")
            if r.error:
                kind, msg, tb = r.error
                print(f"      {color}{kind}: {msg}\033[0m")

    def _summary(self, elapsed):
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        total = len(self.results)
        print()
        print("=" * 50)
        print(f"通过: \033[32m{passed}\033[0m  失败: \033[31m{failed}\033[0m  "
              f"跳过: \033[33m{skipped}\033[0m  总计: {total}  耗时: {elapsed*1000:.1f}ms")
        print("=" * 50)


# ---------- 文件发现 ----------
def discover_files(path):
    if os.path.isfile(path) and path.endswith(".py"):
        return [path]
    found = []
    for root, _, files in os.walk(path):
        for f in files:
            if re.match(r"test_.*\.py$", f) or re.match(r".*_test\.py$", f):
                found.append(os.path.join(root, f))
    return found


def load_module(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- Demo（自带几个测试用例） ----------
def _demo_self_tests():
    """构造一组测试用例并运行"""

    class FakeModule:
        @staticmethod
        def test_simple_pass():
            assert_eq(1 + 1, 2)

        @staticmethod
        def test_simple_fail():
            assert_eq(1 + 1, 3, "math is broken!")

        @staticmethod
        @parametrize("a,b,r", [(1, 2, 3), (2, 3, 5), (10, 20, 30)])
        def test_add(a, b, r):
            assert_eq(a + b, r)

        @staticmethod
        @skip("功能未实现")
        def test_pending():
            assert False

        @staticmethod
        def test_raises():
            assert_raises(ValueError, int, "abc")

    class TestMath:
        def setup(self):
            self.x = 10

        def test_double(self):
            assert_eq(self.x * 2, 20)

        def test_negate(self):
            assert_eq(-self.x, -10)

    # 把 FakeModule 当作模块来收集
    class _Mod:
        pass
    mod = _Mod()
    for n, v in inspect.getmembers(FakeModule):
        if not n.startswith("_"):
            setattr(mod, n, v)
    mod.TestMath = TestMath

    collector = Collector()
    collector.collect_module(mod)
    Runner(verbose=True).run(collector.cases)


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
        files = discover_files(target)
        if not files:
            print("未发现测试文件")
            return
        collector = Collector()
        for fp in files:
            try:
                mod = load_module(fp)
                collector.collect_module(mod)
            except Exception as e:
                print(f"加载 {fp} 失败: {e}")
        ok = Runner(verbose=True).run(collector.cases)
        sys.exit(0 if ok else 1)
    else:
        print("=" * 50)
        print("Mini-pytest Self-Test Demo")
        print("=" * 50)
        _demo_self_tests()


if __name__ == "__main__":
    main()
