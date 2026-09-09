// src/utils/request.js
import axios from 'axios';

// 简单判断环境
const isLocal = window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1';

// 本地开发直连后端3000端口，生产环境用相对路径
const API_BASE_URL = isLocal
    ? `http://${window.location.hostname}:3000/api`
    : '/api';

console.log('环境:', isLocal ? '开发' : '生产');
console.log('API地址:', API_BASE_URL);

const request = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 通义千问API响应较慢，延长到120秒
    headers: {
        'Content-Type': 'application/json'
    }
});

// 请求拦截器
request.interceptors.request.use(
    config => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                const user = JSON.parse(userStr);
                if (user.id) {
                    config.headers['X-User-Id'] = user.id;
                }
            } catch (error) {
                console.warn('解析用户信息失败:', error);
            }
        }
        return config;
    },
    error => Promise.reject(error)
);

// 响应拦截器
request.interceptors.response.use(
    response => {
        if (response.data && typeof response.data === 'object') {
            return response.data;
        }
        return response;
    },
    error => {
        console.error('API请求错误:', error);

        if (!error.response) {
            return Promise.reject({
                code: -1,
                message: '网络连接失败，请检查网络',
                detail: error.message
            });
        }

        const status = error.response.status;
        let message = '请求失败';

        switch(status) {
            case 400:
                message = error.response.data?.message || '请求参数错误';
                break;
            case 401:
                message = '登录已过期，请重新登录';
                localStorage.removeItem('user');
                if (window.location.pathname !== '/login') {
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1500);
                }
                break;
            case 403:
                message = '没有访问权限';
                break;
            case 404:
                message = '请求的资源不存在';
                break;
            case 500:
                message = '服务器内部错误';
                break;
            default:
                message = error.response.data?.message || `请求失败(${status})`;
        }

        return Promise.reject({
            code: status,
            message: message,
            detail: error.response.data
        });
    }
);

export default request;
