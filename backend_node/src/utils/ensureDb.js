// Utility to ensure database exists before Sequelize connects
const mysql = require('mysql2/promise');

async function ensureDatabaseExists() {
  const { DB_HOST, DB_USER, DB_PASSWORD, DB_NAME } = process.env;
  const connection = await mysql.createConnection({
    host: DB_HOST,
    user: DB_USER,
    password: DB_PASSWORD
  });
  await connection.query(`CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\``);
  await connection.end();
}

module.exports = { ensureDatabaseExists };
