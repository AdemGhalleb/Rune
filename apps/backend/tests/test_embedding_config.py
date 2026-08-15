from app.ai.embeddings import config


def test_embedding_model_id_is_deterministic_and_includes_active_configuration():
    model_id = config.get_active_embedding_model_id()

    assert model_id == config.get_active_embedding_model_id()
    assert model_id.startswith(
        f"{config.ACTIVE_EMBEDDING_MODEL_NAME}@{config.ACTIVE_EMBEDDING_DIMENSION}@"
    )
    assert len(model_id.rsplit("@", maxsplit=1)[1]) == 16


def test_embedding_model_id_changes_when_configuration_changes(monkeypatch):
    original = config.get_active_embedding_model_id()
    monkeypatch.setattr(config, "ACTIVE_EMBEDDING_NORMALIZE", False)

    assert config.get_active_embedding_model_id() != original
