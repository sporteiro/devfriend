import axios from 'axios';
import { authService } from './authService';

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';

function getAuthHeaders() {
  const token = authService.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const emailService = {
  /**
   * Obtener las integraciones de email existentes
   * @returns {Promise<Array>}
   */
  async getIntegrations() {
    const response = await axios.get(`${API_URL}/email/integrations`, { 
      headers: getAuthHeaders() 
    });
    return response.data;
  },

  /**
   * Crear una nueva integración de email
   * @param {Object} integrationData 
   * @param {string} integrationData.provider
   * @param {number} integrationData.credential_id
   * @returns {Promise<Object>}
   */
  async createIntegration(integrationData) {
    const response = await axios.post(`${API_URL}/email/integrations`, integrationData, { 
      headers: getAuthHeaders() 
    });
    return response.data;
  },

  /**
   * Eliminar una integración de email
   * @param {number} integrationId
   * @returns {Promise<boolean>}
   */
  async deleteIntegration(integrationId) {
    await axios.delete(`${API_URL}/email/integrations/${integrationId}`, {
      headers: getAuthHeaders(),
    });
    return true;
  },

  /**
   * Obtener emails de una integración
   * @param {number} integrationId
   * @param {Object} params - Parámetros de paginación/filtro
   * @returns {Promise<Array>}
   */
  async getEmails(integrationId, params = {}) {
    const response = await axios.get(`${API_URL}/email/integrations/${integrationId}/emails`, {
      headers: getAuthHeaders(),
      params
    });
    return response.data;
  },

  /**
   * Sincronizar emails (forzar actualización)
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async syncEmails(integrationId) {
    const response = await axios.post(
      `${API_URL}/email/integrations/${integrationId}/sync`, 
      {},
      { headers: getAuthHeaders() }
    );
    return response.data;
  },

  /**
   * Obtener estadísticas de email
   * @param {number} integrationId
   * @returns {Promise<Object>}
   */
  async getStats(integrationId) {
    const response = await axios.get(`${API_URL}/email/integrations/${integrationId}/stats`, {
      headers: getAuthHeaders()
    });
    return response.data;
  }
};