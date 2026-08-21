from __future__ import annotations
import sqlite3
from collections.abc import Iterator, Sequence
from typing import Any
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, ChannelVersions, Checkpoint, CheckpointMetadata, CheckpointTuple, PendingWrite

class DBCheckpointSaver(BaseCheckpointSaver[str]):
    """Persist LangGraph checkpoints in the application's SQLite database."""
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
        checkpoint_id = checkpoint["id"]

        checkpoint_type, checkpoint_data = self.serde.dumps_typed(checkpoint)
        metadata_type, metadata_data = self.serde.dumps_typed(metadata)

        parent_checkpoint_id = configurable.get("checkpoint_id")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO graph_checkpoint(
                checkpoint_id, thread_id, checkpoint_ns, parent_checkpoint_id, checkpoint_type, checkpoint_data, metadata_type, metadata_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?) """,
                (
                    checkpoint_id, thread_id, checkpoint_ns, parent_checkpoint_id, checkpoint_type, checkpoint_data, metadata_type, metadata_data,
                ),
            )
            conn.commit()

        return {"configurable":{"thread_id": thread_id, "checkpoint_ns": checkpoint_ns, "checkpoint_id": checkpoint_id,}}

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        configurable = self._configurable(config)

        thread_id = configurable["thread_id"]
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        checkpoint_id = configurable.get("checkpoint_id")

        if checkpoint_id is None:
            raise ValueError("checkpoint_id is required for writes")

        with self._connect() as conn:
            for write_index, (channel, value) in enumerate(writes):
                value_type, value_data = self.serde.dumps_typed(value)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO graph_checkpoint_write (thread_id, checkpoint_ns, checkpoint_id, task_id,
                        task_path, write_index, channel, value_type, value_data
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id, checkpoint_ns, checkpoint_id, task_id, task_path, write_index,
                        channel, value_type, value_data,
                    ),
                )

            conn.commit()

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        configurable = self._configurable(config)

        thread_id = configurable["thread_id"]
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        checkpoint_id = configurable.get("checkpoint_id")

        with self._connect() as conn:
            if checkpoint_id:
                row = conn.execute(
                    """
                    SELECT * FROM graph_checkpoint
                    WHERE thread_id = ?
                      AND checkpoint_ns = ?
                      AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT *
                    FROM graph_checkpoint
                    WHERE thread_id = ?
                      AND checkpoint_ns = ?
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                ).fetchone()

            if row is None:
                return None

            checkpoint = self.serde.loads_typed(
                (row["checkpoint_type"], row["checkpoint_data"])
            )
            metadata = self.serde.loads_typed(
                (row["metadata_type"], row["metadata_data"])
            )

            writes_rows = conn.execute(
                """
                SELECT
                    channel,
                    value_type,
                    value_data
                FROM graph_checkpoint_write
                WHERE thread_id = ?
                  AND checkpoint_ns = ?
                  AND checkpoint_id = ?
                ORDER BY write_index
                """,
                (
                    thread_id,
                    checkpoint_ns,
                    row["checkpoint_id"],
                ),
            ).fetchall()

        pending_writes: list[PendingWrite] = []

        for write_row in writes_rows:
            value = self.serde.loads_typed(
                (
                    write_row["value_type"],
                    write_row["value_data"],
                )
            )
            pending_writes.append(
                ("", write_row["channel"], value)
            )

        result_config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": row["checkpoint_id"],
            }
        }

        parent_config = None

        if row["parent_checkpoint_id"]:
            parent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": row["parent_checkpoint_id"],
                }
            }

        return CheckpointTuple(
            config=result_config,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=pending_writes,
        )

    def list(self, config: RunnableConfig | None, *, filter: dict[str, Any] | None = None, before: RunnableConfig | None = None, limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        thread_id = None
        Checkpoint_ns = ""

        if config:
            configurable = self._configurable(config)
            thread_id = configurable.get("thread_id")
            checkpoint_ns = configurable.get("checkpoint_ns", "")

        query = """
            SELECT *
            FROM graph_checkpoint
            WHERE 1 = 1
        """

        params: list[Any] = []

        if thread_id is not None:
            query += " AND thread_id = ?"
            params.append(thread_id)

        query += " AND checkpoint_ns = ?"
        params.append(checkpoint_ns)

        if before:
            before_id = self._configurable(before).get("checkpoint_id")
            if before_id:
                query += """
                    AND rowid < (
                        SELECT rowid
                        FROM graph_checkpoint
                        WHERE checkpoint_id = ?
                    )
                """
                params.append(before_id)

        query += " ORDER BY rowid DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

            for row in rows:
                checkpoint = self.serde.loads_typed(
                    (
                        row["checkpoint_type"],
                        row["checkpoint_data"],
                    )
                )
                metadata = self.serde.loads_typed(
                    (
                        row["metadata_type"],
                        row["metadata_data"],
                    )
                )

                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": row["thread_id"],
                            "checkpoint_ns": row["checkpoint_ns"],
                            "checkpoint_id": row["checkpoint_id"],
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=(
                        {
                            "configurable": {
                                "thread_id": row["thread_id"],
                                "checkpoint_ns": row["checkpoint_ns"],
                                "checkpoint_id": row["parent_checkpoint_id"],
                            }
                        }
                        if row["parent_checkpoint_id"]
                        else None
                    ),
                    pending_writes=[],
                )

    def delete_thread(self, thread_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM graph_checkpoint_write
                WHERE thread_id = ?
                """,
                (thread_id,),
            )

            conn.execute(
                """
                DELETE FROM graph_checkpoint
                WHERE thread_id = ?
                """,
                (thread_id,),
            )

            conn.commit()

    def get_next_version(self, current: str | None, channel: None = None) -> str:
        if current is None:
            return "1"

        try:
            return str(int(current) + 1)
        except ValueError:
            return f"{current}.1"

