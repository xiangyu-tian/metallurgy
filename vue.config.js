const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
    transpileDependencies: true,
    publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',

    // 生产环境输出到dist文件夹
    outputDir: 'dist',
    assetsDir: 'static',

    // 开发服务器配置
    devServer: {
        port: 8080,
        proxy: {
            '/api': {
                target: 'http://localhost:3000',
                changeOrigin: true,
                pathRewrite: { '^/api': '/api' }
            }
        },
        historyApiFallback: true 
    },

    // 生产环境关闭source map
    productionSourceMap: false,

    // 防止copy-webpack-plugin与html-webpack-plugin冲突
    chainWebpack: config => {
        config.plugin('copy').tap(([options]) => {
            options.patterns[0].globOptions = { ignore: ['**/index.html'] };
            return [options];
        });
    },

    // 配置Webpack
    configureWebpack: {
        resolve: {
            fallback: {
                "path": require.resolve("path-browserify"),
                "os": require.resolve("os-browserify/browser"),
                "crypto": require.resolve("crypto-browserify"),
                "stream": require.resolve("stream-browserify"),
                "buffer": require.resolve("buffer/"),
            }
        }
    }
});