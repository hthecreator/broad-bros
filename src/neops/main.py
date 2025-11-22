import typer

app = typer.Typer()


@app.command()
def hello(name: str):
    """Say hello to someone"""
    print(f"Hello {name}")


# Add more commands here as needed
# @app.command()
# def another_command():
#     pass


def main():
    app()


if __name__ == "__main__":
    main()
