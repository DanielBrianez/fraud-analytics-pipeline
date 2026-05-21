SELECT
    category,
    COUNT(*) AS total_transacoes,
    SUM(CAST(is_fraud AS INTEGER)) AS total_fraudes,
    ROUND(AVG(CAST(is_fraud AS REAL)) * 100, 4) AS taxa_fraude

FROM transactions
GROUP BY category
ORDER BY taxa_fraude DESC;