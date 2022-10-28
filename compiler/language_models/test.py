import traceback
import typing


def test(test_class):
    print(f'testing {test_class}')
    instance = test_class()

    for name in dir(test_class):
        method = getattr(instance, name)
        if name.startswith('test_') and isinstance(method, typing.Callable):
            print(f'    {name}:')

            try:
                method()
            except AssertionError:
                print('        FAILURE')
                traceback.print_exc()
            except Exception:  # noqa, pylint: disable=broad-except
                print('        ERROR')
                traceback.print_exc()
            else:
                print('        SUCCESS')
