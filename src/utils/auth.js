// src/utils/auth.js

// 获取当前用户信息
export function getCurrentUser() {
    try {
        const userStr = localStorage.getItem('user');
        if (!userStr) return null;

        return JSON.parse(userStr);
    } catch (error) {
        console.error('解析用户信息失败:', error);
        return null;
    }
}

// 检查是否已登录
export function isLoggedIn() {
    return localStorage.getItem('isLoggedIn') === 'true' && getCurrentUser() !== null;
}

// 检查是否是管理员
// auth.js - 修改 isAdmin 函数
export function isAdmin() {
    const user = getCurrentUser();
    if (!user) return false;

    // ========== 修改这里：根据 account_type 或 role 判断管理员 ==========
    return (
        (user.accountType && user.accountType.toLowerCase() === 'admin') ||
        (user.role && user.role.toLowerCase() === 'admin')
    );
}

// 修改 getUserRole 函数
export function getUserRole() {
    const user = getCurrentUser();
    if (!user) return 'guest';

    // ========== 修改这里：根据 account_type 或 role 判断管理员 ==========
    if ((user.accountType && user.accountType.toLowerCase() === 'admin') ||
        (user.role && user.role.toLowerCase() === 'admin')) {
        return 'admin';
    }
    
    return 'user';
}

// 获取显示名称（优先使用真实姓名，然后是用户名，最后是邮箱）
export function getDisplayName() {
    const user = getCurrentUser();
    if (!user) return '';

    if (user.realName && user.realName.trim()) {
        return user.realName;
    } else if (user.username && user.username.trim()) {
        return user.username;
    } else {
        return user.email ? user.email.split('@')[0] : '';
    }
}

// 获取用户邮箱
export function getUserEmail() {
    const user = getCurrentUser();
    return user ? user.email : '';
}

// 获取用户头像首字母（用于显示头像）
export function getUserAvatar() {
    const displayName = getDisplayName();
    if (!displayName) return 'U';

    return displayName.charAt(0).toUpperCase();
}

// 获取用户角色标签（中文显示）
export function getRoleLabel() {
    const role = getUserRole();
    switch(role) {
        case 'admin':
            return '管理员';
        case 'user':
            return '用户';
        default:
            return '游客';
    }
}

// 注销
export function logout() {
    localStorage.removeItem('user');
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('isAdmin');
    localStorage.removeItem('userRole');
    localStorage.removeItem('rememberMe');
    localStorage.removeItem('userEmail');

    // 跳转到登录页
    window.location.href = '/login';
}

// 检查是否有权限访问特定功能（基于角色）
export function hasPermission(requiredRole) {
    const userRole = getUserRole();
    const roleHierarchy = {
        'guest': 0,
        'user': 1,
        'admin': 2
    };

    const userLevel = roleHierarchy[userRole] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;

    return userLevel >= requiredLevel;
}