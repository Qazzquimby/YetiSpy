def outer_func():
    def main():
        inner_func()

    def inner_func():
        assert False

    main()


if __name__ == '__main__':
    outer_func()
