PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS es_service (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL UNIQUE,
  description TEXT,
  price NUMERIC NOT NULL DEFAULT 0,
  created_by INTEGER NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS es_service_item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  service_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  unit_price NUMERIC NOT NULL DEFAULT 0,
  FOREIGN KEY(service_id) REFERENCES es_service(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS es_service_task (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  service_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  assigned_to INTEGER,
  status TEXT NOT NULL DEFAULT "Pending",
  due_date DATETIME,
  FOREIGN KEY(service_id) REFERENCES es_service(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_es_service_created_at ON es_service(created_at);
CREATE INDEX IF NOT EXISTS idx_es_service_item_service_id ON es_service_item(service_id);
CREATE INDEX IF NOT EXISTS idx_es_service_task_service_id ON es_service_task(service_id);

