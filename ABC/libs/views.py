import keg_elements.views
from blazeutils import strings
from keg.web import BaseView as _BaseView


class BaseView(_BaseView):
    def calc_class_fname(self):
        return strings.case_cw2dash(self.__class__.__name__)


class DependencyError(Exception):
    pass


class GridView(keg_elements.views.GridView):
    template = 'includes/grid-view.html'
