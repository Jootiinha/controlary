-- Create test user for development
INSERT INTO users (id, username, email, password_hash, full_name, is_active, created_at, updated_at)
VALUES (
    'test-user-001',
    'testuser',
    'testuser@example.com',
    '$2b$12$oXx01hB47YO/Sgo0Ou9XuucaIdEGsnXVhat8TkR2Sm3uqeFjqISta',
    'Test User',
    1,
    datetime('now'),
    datetime('now')
)
ON CONFLICT(username) DO NOTHING;
