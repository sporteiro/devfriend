import axios from 'axios';
import { authService } from './authService';

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';

function getAuthHeaders() {
  const token = authService.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const messagesService = {
  /**
   * Obtener las integraciones de Messages/Slack existentes
   * @returns {Promise<Array>}
   */
  async getIntegrations() {
    const response = await axios.get(`${API_URL}/messages/integrations`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  /**
   * Crear una nueva integración de Messages/Slack
   * @param {Object} integrationData
   * @param {number} integrationData.credential_id
   * @returns {Promise<Object>}
   */
  async createIntegration(integrationData) {
    const response = await axios.post(`${API_URL}/messages/integrations`, integrationData, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  /**
   * Eliminar una integración de Messages/Slack
   * @param {number} integrationId
   * @returns {Promise<boolean>}
   */
  async deleteIntegration(integrationId) {
    await axios.delete(`${API_URL}/messages/integrations/${integrationId}`, {
      headers: getAuthHeaders(),
    });
    return true;
  },

  /**
   * Obtener mensajes de una integración
   * @param {number} integrationId
   * @param {Object} params - Parámetros de paginación/filtro
   * @returns {Promise<Array>}
   */
  async getMessages(integrationId, params = {}) {
    const response = await axios.get(`${API_URL}/messages/integrations/${integrationId}/messages`, {
      headers: getAuthHeaders(),
      params
    });
    return response.data;
  },

  /**
   * Obtener canales de una integración
   * @param {number} integrationId
   * @returns {Promise<Array>}
   */
  async getChannels(integrationId) {
    const response = await axios.get(`${API_URL}/messages/integrations/${integrationId}/channels`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  /**
   * Sync Messages/Slack data (force update)
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async syncMessages(integrationId) {
    const response = await axios.post(
      `${API_URL}/messages/integrations/${integrationId}/sync`,
      {},
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  /**
   * Obtener estadísticas de Messages/Slack
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async getStats(integrationId) {
    const response = await axios.get(`${API_URL}/messages/integrations/${integrationId}/stats`, {
      headers: getAuthHeaders()
    });
    return response.data;
  }
};
