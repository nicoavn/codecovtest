import pathlib
import warnings

from sqlalchemy.exc import SAWarning

warnings.filterwarnings('error', '.*Unicode type received non-unicode.*', category=SAWarning)

src_dpath = pathlib.Path(__file__).parent.parent
