const { Module } = require('@nestjs/common');
const { TypeOrmModule } = require('@nestjs/typeorm');
const { Auth } = require('./controller/Auth');
const { Auth: AuthService } = require('./service/Auth');
const { UserRepo } = require('./repo/User');
const { User } = require('./entity/User');
const { DatabaseConfig } = require('./config/DatabaseConfig');

const AppModule = Module({
    imports: [
        TypeOrmModule.forRoot(DatabaseConfig),
        TypeOrmModule.forFeature([User]),
    ],
    controllers: [Auth],
    providers: [AuthService, UserRepo],
})(class {});

module.exports = { AppModule };