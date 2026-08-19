from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from typing import Any

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from langchain_core.runnables import RunnableConfig


class DBCheckpointSaver(BaseCheckpointSaver):
    """Persist LangGraph checkpoints in the repository SQLite schema."""

    def __init__(self, database_path: str) -> None:
        super().__init__()
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _configurable(config: RunnableConfig) -> dict[str, Any]:
        return config.get("configurable", {})

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        configurable = self._configurable(config)
        thread_id = configurable["thread_id"]
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        parent_checkpoint_id = configurable.get("checkpoint_id")
        checkpoint_type, checkpoint_data = self.serde.dumps_typed(checkpoint)
        metadata_type, metadata_data = self.serde.dumps_typed(metadata)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO graph_checkpoint(
                    checkpoint_id, thread_id, checkpoint_ns,
                    parent_checkpoint_id, checkpoint_type, checkpoint_data,
                    metadata_type, metadata_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint["id"],
                    thread_id,
                    checkpoint_ns,
                    parent_checkpoint_id,
                    checkpoint_type,
                    checkpoint_data,
                    metadata_type,
                    metadata_data,
                ),
            )
            connection.commit()

        return {
            **config,
            "configurable": {
                **configurable,
                "checkpoint_id": checkpoint["id"],
            },
        }

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        configurable = self._configurable(config)
        thread_id = configurable["thread_id"]
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        checkpoint_id = configurable.get("checkpoint_id")

        with self._connect() as connection:
            if checkpoint_id:
                row = connection.execute(
                    """
                    SELECT * FROM graph_checkpoint
                    WHERE thread_id = ? AND checkpoint_ns = ?
                      AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM graph_checkpoint
                    WHERE thread_id = ? AND checkpoint_ns = ?
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                ).fetchone()

        if row is None:
            return None

        with self._connect() as connection:
            write_rows = connection.execute(
                """
                SELECT task_id, channel, value_type, value_data
                FROM graph_checkpoint_write
                WHERE thread_id = ? AND checkpoint_ns = ?
                  AND checkpoint_id = ?
                ORDER BY write_index
                """,
                (row["thread_id"], row["checkpoint_ns"], row["checkpoint_id"]),
            ).fetchall()

        parent_config = None
        if row["parent_checkpoint_id"]:
            parent_config = {
                "configurable": {
                    "thread_id": row["thread_id"],
                    "checkpoint_ns": row["checkpoint_ns"],
                    "checkpoint_id": row["parent_checkpoint_id"],
                }
            }

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": row["thread_id"],
                    "checkpoint_ns": row["checkpoint_ns"],
                    "checkpoint_id": row["checkpoint_id"],
                }
            },
            checkpoint=self.serde.loads_typed(
                (row["checkpoint_type"], row["checkpoint_data"])
            ),
            metadata=self.serde.loads_typed(
                (row["metadata_type"], row["metadata_data"])
            ),
            parent_config=parent_config,
            pending_writes=[
                (
                    write_row["task_id"],
                    write_row["channel"],
                    self.serde.loads_typed(
                        (write_row["value_type"], write_row["value_data"])
                    ),
                )
                for write_row in write_rows
            ],
        )

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        configurable = self._configurable(config)
        checkpoint_id = configurable.get("checkpoint_id")
        if not checkpoint_id:
            return

        with self._connect() as connection:
            for write_index, (channel, value) in enumerate(writes):
                value_type, value_data = self.serde.dumps_typed(value)
                connection.execute(
                    """
                    INSERT OR REPLACE INTO graph_checkpoint_write(
                        thread_id, checkpoint_ns, checkpoint_id,
                        task_id, task_path, write_index, channel,
                        value_type, value_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        configurable["thread_id"],
                        configurable.get("checkpoint_ns", ""),
                        checkpoint_id,
                        task_id,
                        task_path,
                        write_index,
                        channel,
                        value_type,
                        value_data,
                    ),
                )
            connection.commit()

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        if config is None:
            return iter(())

        configurable = self._configurable(config)
        query = "SELECT * FROM graph_checkpoint WHERE thread_id = ?"
        parameters: list[Any] = [configurable["thread_id"]]
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        query += " AND checkpoint_ns = ?"
        parameters.append(checkpoint_ns)
        query += " ORDER BY created_at DESC, rowid DESC"
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        for row in rows:
            checkpoint_config = {
                "configurable": {
                    "thread_id": row["thread_id"],
                    "checkpoint_ns": row["checkpoint_ns"],
                    "checkpoint_id": row["checkpoint_id"],
                }
            }
            yield CheckpointTuple(
                config=checkpoint_config,
                checkpoint=self.serde.loads_typed(
                    (row["checkpoint_type"], row["checkpoint_data"])
                ),
                metadata=self.serde.loads_typed(
                    (row["metadata_type"], row["metadata_data"])
                ),
                parent_config=None,
                pending_writes=[],
            )
