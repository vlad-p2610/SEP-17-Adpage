ATTACH TABLE _ UUID 'f7a73f4a-d63a-4cd1-95d5-d4e0af3e095d'
(
    `id` UInt32,
    `name` String,
    `value` Float64
)
ENGINE = MergeTree
ORDER BY id
SETTINGS index_granularity = 8192
