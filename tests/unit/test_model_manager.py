from unittest.mock import Mock

import pytest

from polyocr.api.errors import ServiceError
from polyocr.services.model_manager import ModelManager


def test_same_paddle_code_reuses_model() -> None:
    factory = Mock(return_value=object())
    manager = ModelManager(factory)
    assert manager.get("zh") is manager.get("中文")
    factory.assert_called_once_with(lang="ch")


def test_load_failure_is_not_cached() -> None:
    factory = Mock(side_effect=[RuntimeError("boom"), object()])
    manager = ModelManager(factory)
    with pytest.raises(ServiceError, match="could not be loaded"):
        manager.get("en")
    assert manager.get("en") is not None
    assert factory.call_count == 2
