import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import ComponentsPage from './pages/ComponentsPage';
import ComponentDetailPage from './pages/ComponentDetailPage';
import ComponentFormPage from './pages/ComponentFormPage';
import MappingsPage from './pages/MappingsPage';
import MappingFormPage from './pages/MappingFormPage';
import EnvironmentMatrixPage from './pages/EnvironmentMatrixPage';
import EnvironmentsManagementPage from './pages/EnvironmentsManagementPage';
import CategoriesManagementPage from './pages/CategoriesManagementPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/components" element={<ComponentsPage />} />
        <Route path="/components/new" element={<ComponentFormPage />} />
        <Route path="/components/:id/edit" element={<ComponentFormPage />} />
        <Route path="/components/:id" element={<ComponentDetailPage />} />
        <Route path="/mappings" element={<MappingsPage />} />
        <Route path="/mappings/new" element={<MappingFormPage />} />
        <Route path="/mappings/:id/edit" element={<MappingFormPage />} />
        <Route path="/environments" element={<EnvironmentsManagementPage />} />
        <Route path="/categories" element={<CategoriesManagementPage />} />
        <Route path="/matrix" element={<EnvironmentMatrixPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
