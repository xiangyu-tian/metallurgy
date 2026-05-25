const DatabaseConfig = {
    type: 'postgres',
    host: '192.168.31.145',
    port: 5432,
    username: 'postgres',
    password: 'WJwzfwJ5JeXSkJ66',
    database: 'metallurgy',
    entities: [__dirname + '/../entity/*.js'],
    synchronize: true,
};

module.exports = { DatabaseConfig };