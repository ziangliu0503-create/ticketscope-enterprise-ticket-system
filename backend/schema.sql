PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('requester', 'agent', 'admin')),
    password_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_no TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    department TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    status TEXT NOT NULL CHECK (status IN ('NEW', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
    requester_id INTEGER NOT NULL,
    assignee_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT,
    escalation_level INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (requester_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ticket_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    operator_id INTEGER,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_department ON tickets(department);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_ticket_logs_ticket ON ticket_logs(ticket_id);
