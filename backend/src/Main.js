const { NestFactory } = require('@nestjs/core');
const { AppModule } = require('./AppModule');

async function bootstrap() {
    const app = await NestFactory.create(AppModule);
    await app.listen(3000);
    console.log('冶金平台后端运行在 http://localhost:3000');
}
bootstrap();