# Campus Byte

A campus food-delivery capstone built with React, React Router DOM, FastAPI, SQLAlchemy and SQLite. Customers order from a kitchen, owners decide which orders to accept, and delivery partners take meals to the requested campus location.

## Run the application

Install Docker Desktop (or Docker Engine with Docker Compose) and start Docker. From the directory containing compose.yaml:

1. Create a file called `.env` beside compose.yaml with one line, `JWT_SECRET=<your-random-secret>`. To generate the entire file with Python 3, run the command below. On Windows use `py` if needed.
2. Start both containers.
3. Open **http://localhost:8080**. Choose **Create an account**. A new database starts empty.

```sh
python -c "import pathlib,secrets; pathlib.Path('.env').write_text('JWT_SECRET='+secrets.token_hex(32))"
docker compose up --build -d
```

Use `docker compose logs backend` for API errors and `docker compose down` to stop. SQLite lives in the named volume `campus_data` and survives normal stops and rebuilds. Keep the same secret across restarts to keep existing sessions valid.

## Demonstrate the three roles

Use three tabs opened independently at localhost:8080. Each tab keeps its own login in session storage. Use a different email for each role.

| Role | Action | Expected result |
|---|---|---|
| Restaurant owner | Register a kitchen, add Masala Dosa at ₹65. | The customer menu shows the dish. |
| Delivery partner | Register and open Deliveries. | The rider is eligible for an assignment. |
| Customer | Choose the kitchen, add two dosas, enter a room and submit. | An order for ₹130 appears with “Awaiting kitchen”. |
| Owner | Open Orders and accept. | An idle rider receives the ticket. |
| Partner | Confirm pickup, then mark delivered. | The customer sees “On the way” and then “Delivered”. |

Try a second order and reject it. It ends as **Declined**. To test the queue, accept two orders with only one rider. The second one stays waiting until the rider delivers the first. The app polls orders every four seconds.

## How a request moves through the application

React Router renders the page for the signed-in role. The checkout form sends dish IDs, quantities and a delivery location to FastAPI. The server loads active dishes from one restaurant, calculates their total in integer paise, and saves the order and its lines in one transaction. It copies the price and dish name to each order line so future menu edits preserve the receipt.

The API verifies a signed, eight-hour JWT and loads the account role from SQL on each protected request. Owner queries are scoped to their restaurant. Riders can only update orders assigned to them. Customers see their own orders. Passwords use salted scrypt hashes. Self-registration for all three roles is a capstone design choice.

| Current state | Allowed action | Next state |
|---|---|---|
| Requested | Owner accepts or rejects | Waiting or rejected |
| Waiting | Dispatcher reserves an idle rider | Assigned |
| Assigned | Assigned rider confirms pickup | Picked up |
| Picked up | Assigned rider confirms delivery | Delivered |

A FastAPI background task runs after acceptance, rider registration and delivery. It pairs the oldest waiting orders with idle riders under a SQLite write lock. All registered riders without an active assignment are treated as available. Startup also runs dispatch to recover pending work after a restart. Invalid transitions return HTTP 409.

## Source map and data model

| Path | Responsibility |
|---|---|
| frontend/src/main.jsx, Auth.jsx | Routing, session state, registration, sign-in |
| frontend/src/Kitchens.jsx | Menu, cart, quantity controls and checkout |
| frontend/src/Menu.jsx, Orders.jsx | Owner menu CRUD, tickets and delivery progress |
| frontend/src/api.js | Authenticated HTTP requests and INR formatting |
| backend/auth.py | Password hashing, JWT creation, authentication and role checks |
| backend/main.py | API routes, checkout rules and background dispatch |
| backend/db.py, schema.sql | SQLAlchemy ORM mappings, SQLite constraints and transaction handling |
| tests/ | API regression tests and a three-session browser walkthrough |
| compose.yaml, frontend/nginx.conf | Containers, persistent volume and same-origin routing |

One owner has one restaurant. Each restaurant has many dishes and orders. Each order belongs to one customer, has many order lines, and can have one assigned rider. Removing a dish hides it from checkout while retaining its historical references.

## REST endpoints

| Method and path | Access | Purpose |
|---|---|---|
| POST /api/register, POST /api/login | Public | Create an account or sign in |
| GET /api/health, GET /api/restaurants | Public | Service status and available menus |
| GET /api/menu, POST /api/menu | Owner | List or add dishes |
| PUT or DELETE /api/menu/{dish_id} | Owning restaurant | Edit or retire a dish |
| POST /api/orders | Customer | Place an order |
| GET /api/orders | Signed-in account | List role-scoped tickets |
| POST /api/orders/{id}/accept or /reject | Owning restaurant | Decide on a request |
| POST /api/orders/{id}/pickup or /deliver | Assigned rider | Advance a delivery |

## Local development and testing

With Python 3.12 and Node.js 22, use a virtual environment and install the backend dependencies. Set JWT_SECRET in the shell environment using a random value of at least 32 characters. Run the following from the repository root:

```sh
python -m pip install -r backend/requirements.txt httpx==0.28.1
python -m unittest discover -s tests -v
python -m uvicorn backend.main:app --reload
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite. Its development proxy sends /api requests to port 8000. FastAPI's interactive endpoint reference is at http://localhost:8000/docs during local development. The Docker build serves the compiled React files through Nginx and proxies /api to the backend container.

GitHub Actions runs the API tests, builds both containers, and exercises registration, menu creation, checkout, acceptance, pickup and delivery in isolated mobile-sized Chromium sessions. Run that browser test locally against a **fresh disposable Compose database** with `pip install playwright==1.55.0`, `python -m playwright install chromium` and `python tests/browser_flow.py`.

## Publish the repository for submission

The downloadable archive includes the Git repository and its feature commits. Extract it completely before opening the campus-byte folder. Run `git log --oneline` to see the history. With GitHub CLI installed and signed into your account:

```sh
gh auth login
gh repo create campus-byte --public --source=. --remote=origin --push
gh repo view --json url,visibility
```

If campus-byte already exists in your account, choose an unused repository name in the create command. Check that visibility is PUBLIC, open the Actions tab for the integration result, then submit the repository URL in NMS.
