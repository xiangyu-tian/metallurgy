'use strict';

// 实验平台使用独立端口，避免影响正式聊天服务。
process.env.PORT = process.env.EXPERIMENT_PORT || '3001';
require('./server');
