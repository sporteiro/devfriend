import axios from 'axios';
import { authService } from './authService';

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';

function getAuthHeaders() {
  const token = authService.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const githubService = {
  /**
   * Obtener las integraciones de GitHub existentes
   * @returns {Promise<Array>}
   */
  async getIntegrations() {
    const response = await axios.get(`${API_URL}/github/integrations`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  /**
   * Crear una nueva integración de GitHub
   * @param {Object} integrationData
   * @param {number} integrationData.credential_id
   * @returns {Promise<Object>}
   */
  async createIntegration(integrationData) {
    const response = await axios.post(`${API_URL}/github/integrations`, integrationData, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  /**
   * Eliminar una integración de GitHub
   * @param {number} integrationId
   * @returns {Promise<boolean>}
   */
  async deleteIntegration(integrationId) {
    await axios.delete(`${API_URL}/github/integrations/${integrationId}`, {
      headers: getAuthHeaders(),
    });
    return true;
  },

  /**
   * Obtener repositorios de una integración
   * @param {number} integrationId
   * @param {Object} params - Parámetros de paginación/filtro
   * @returns {Promise<Array>}
   */
  async getRepos(integrationId, params = {}) {
    const response = await axios.get(`${API_URL}/github/integrations/${integrationId}/repos`, {
      headers: getAuthHeaders(),
      params
    });
    return response.data;
  },

  /**
   * Obtener perfil de usuario de GitHub
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async getUserProfile(integrationId) {
    const response = await axios.get(`${API_URL}/github/integrations/${integrationId}/user`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  /**
   * Sync GitHub data (force update)
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async syncGithub(integrationId) {
    const response = await axios.post(
      `${API_URL}/github/integrations/${integrationId}/sync`,
      {},
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  /**
   * Obtener estadísticas de GitHub
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async getStats(integrationId) {
    const response = await axios.get(`${API_URL}/github/integrations/${integrationId}/stats`, {
      headers: getAuthHeaders()
    });
    return response.data;
  }
};
