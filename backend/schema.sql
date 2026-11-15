CREATE TABLE IF NOT EXISTS Account (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('customer','owner','partner'))
);
CREATE TABLE IF NOT EXISTS Restaurant (
 id INTEGER PRIMARY KEY, owner INTEGER NOT NULL UNIQUE REFERENCES Account, name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Dish (
 id INTEGER PRIMARY KEY, restaurant INTEGER NOT NULL REFERENCES Restaurant,
 name TEXT NOT NULL, paise INTEGER NOT NULL CHECK(paise>0), active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS Purchase (
 id INTEGER PRIMARY KEY, customer INTEGER NOT NULL REFERENCES Account, restaurant INTEGER NOT NULL REFERENCES Restaurant,
 address TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'requested'
 CHECK(status IN ('requested','rejected','waiting','assigned','picked_up','delivered')),
 partner INTEGER REFERENCES Account, total INTEGER NOT NULL,
 created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS OrderLine (
 purchase INTEGER NOT NULL REFERENCES Purchase, dish INTEGER NOT NULL REFERENCES Dish,
 name TEXT NOT NULL, paise INTEGER NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0),
 PRIMARY KEY(purchase,dish)
);
CREATE INDEX IF NOT EXISTS purchase_dispatch ON Purchase(status, id);
