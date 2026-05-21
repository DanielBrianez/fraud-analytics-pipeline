SELECT
    CASE
        WHEN CAST(strftime('%H', trans_date_trans_time) AS INTEGER) BETWEEN 0 AND 5
            THEN 'Madrugada'
        WHEN CAST(strftime('%H', trans_date_trans_time) AS INTEGER) BETWEEN 6 AND 11
            THEN 'Manhã'
        WHEN CAST(strftime('%H', trans_date_trans_time) AS INTEGER) BETWEEN 12 AND 17
            THEN 'Tarde'
        ELSE 'Noite'
    END AS periodo_dia,

    COUNT(*) AS total_transacoes,
    SUM(CAST(is_fraud AS INTEGER)) AS total_fraudes,
    ROUND(AVG(CAST(is_fraud AS REAL)) * 100, 4) AS taxa_fraude

FROM transactions
GROUP BY periodo_dia
ORDER BY taxa_fraude DESC;