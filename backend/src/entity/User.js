const { Entity, Column, PrimaryGeneratedColumn } = require('typeorm');

const User = Entity('users')(class {
    constructor() {
        this.id = PrimaryGeneratedColumn()();
        this.username = Column({ unique: true })();
        this.email = Column({ unique: true })();
        this.password = Column()();
        this.realName = Column({ nullable: true })();
        this.organization = Column({ nullable: true })();
        this.createdAt = Column({ default: () => 'CURRENT_TIMESTAMP' })();
    }
});

module.exports = { User };