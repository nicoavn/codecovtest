import webgrid
import webgrid.flask


class GridManager(webgrid.flask.WebGrid):
    args_loaders = (
        webgrid.extensions.RequestArgsLoader,
        webgrid.extensions.RequestFormLoader,
        webgrid.extensions.WebSessionArgsLoader,
    )


class Grid(webgrid.BaseGrid):
    manager = GridManager()
