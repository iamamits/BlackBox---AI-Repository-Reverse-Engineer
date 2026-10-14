# BlackBox app package
import typing
import sqlalchemy.util.typing

# Python 3.14 compatibility patch for SQLAlchemy typing
_orig_make_union = sqlalchemy.util.typing.make_union_type


def _py314_make_union_type(*types):
    try:
        return _orig_make_union(*types)
    except TypeError:
        return typing.Union[types]


sqlalchemy.util.typing.make_union_type = _py314_make_union_type
