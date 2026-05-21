SELECT
    is_fraud,
    COUNT(*) AS total_transacoes,
    ROUND(
        COUNT(*) * 100.0 / (
            SELECT COUNT(*)
            FROM transactions
        ),
        4
    ) AS percentual

FROM transactions
GROUP BY is_fraud
ORDER BY is_fraud;