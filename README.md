# Flow Radar - Traffic Analytics & Monitoring Platform

A comprehensive React-based frontend application for traffic analytics and monitoring with multiple user roles.

## Features

- **4 User Roles**: Public, Government, System Developer (Admin), and Traffic Analyst
- **Real-time Maps**: Interactive Leaflet maps with congestion visualization
- **Role-based Dashboards**: Customized interfaces for each user type
- **Mock Data Integration**: Complete frontend with simulated API calls
- **Responsive Design**: Mobile-friendly with Tailwind CSS

## Tech Stack

- **React 18** with Vite
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Leaflet & React Leaflet** for maps
- **Recharts** for data visualization
- **React Icons** for icons

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

## User Roles & Routes

### Public User
- Dashboard: `/public/dashboard`
- Live Congestion Map: `/public/map`
- Route Traffic Status: `/public/route-status`
- Daily Top Hotspots: `/public/hotspots`
- Report Incident: `/public/report-incident`
- Feedback: `/public/feedback`

### Government User
- Dashboard: `/gov/dashboard`
- Congestion Heatmap: `/gov/heatmap`
- Input Roadwork Event: `/gov/roadwork`
- EMAS Incident Status: `/gov/emas`
- Critical Alerts: `/gov/alerts`
- Time-based Reports: `/gov/reports`
- Event Simulation: `/gov/simulation`
- Weather Overlay: `/gov/weather`
- Public Transport Overlay: `/gov/transport`
- Manage User Accounts: `/gov/manage-users`

### System Developer (Admin)
- Algorithm Modules: `/dev/algorithms`
- System Performance: `/dev/performance`
- Access Roles: `/dev/access-roles`
- Feedback Management: `/dev/feedback`
- Maintenance & Logs: `/dev/logs`
- Visualization Modules: `/dev/visualization`
- Backup & Restore: `/dev/backup`
- API Integrations: `/dev/integrations`
- Deployments: `/dev/deployments`

### Traffic Analyst
- Data Preprocessing: `/analyst/preprocess`
- Run Traffic Flow Model: `/analyst/run-model`
- View Historical Trends: `/analyst/trends`
- Schedule Automated Runs: `/analyst/schedule`

## Login

Access the login page at `/login`. You can:
- Select a role (Public, Government, Developer, Analyst)
- Enter email and password (mock validation)
- For Public users: Use "Continue as Guest" for quick access
- For Government users: Optional 2FA token field

## Project Structure

```
src/
  api/          # Mock API functions and data
  components/   # Reusable UI components
  context/      # React context (Auth)
  layouts/      # Layout components
  pages/        # Page components organized by role
  router/       # Routing configuration
  styles/       # Global styles and Tailwind config
```

## Mock Data

All data is mocked using:
- Static JSON data in `src/api/mockData.js`
- Simulated API delays in `src/api/mockApi.js`
- No real backend connections required

## Notes

- This is a UI-only implementation with no real backend
- All API calls are simulated with setTimeout
- User authentication is frontend-only (localStorage)
- Maps use OpenStreetMap tiles
- All data is static/mock data

## License

ISC

