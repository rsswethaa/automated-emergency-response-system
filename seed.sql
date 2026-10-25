INSERT INTO incidents (latitude, longitude, impact_g, motion_after_impact, severity, status) VALUES
(-36.8485, 174.7633, 2.8, 1, 'MEDIUM', 'RESOLVED'),
(-36.8509, 174.7645, 6.4, 0, 'CRITICAL', 'OPEN');

INSERT INTO alerts (incident_id, recipient, channel, message) VALUES
(1, 'demo-responder', 'SIMULATED', 'Sample resolved incident for dashboard demonstration.'),
(2, 'demo-responder', 'SIMULATED', 'Sample critical incident for dashboard demonstration.');
