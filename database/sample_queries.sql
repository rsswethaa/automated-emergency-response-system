-- Recent incidents
SELECT id, severity, status, impact_g, latitude, longitude, created_at
FROM incidents
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Open incidents by severity
SELECT severity, COUNT(*) AS incident_count
FROM incidents
WHERE status = 'OPEN'
GROUP BY severity
ORDER BY CASE severity
    WHEN 'CRITICAL' THEN 1
    WHEN 'HIGH' THEN 2
    WHEN 'MEDIUM' THEN 3
    ELSE 4
END;

-- Incident and alert audit trail
SELECT
    i.id AS incident_id,
    i.severity,
    i.status,
    a.channel,
    a.recipient,
    a.message,
    a.sent_at
FROM incidents AS i
LEFT JOIN alerts AS a ON a.incident_id = i.id
ORDER BY i.id DESC, a.id DESC;

-- Average simulated impact by severity
SELECT severity, ROUND(AVG(impact_g), 2) AS average_impact_g
FROM incidents
GROUP BY severity;
