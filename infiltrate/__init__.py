from infiltrate.app import create_app

app, db = create_app()


def update():
    import infiltrate.models
    infiltrate.models.update()


if __name__ == '__main__':
    update()
