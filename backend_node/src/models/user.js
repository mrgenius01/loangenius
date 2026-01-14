// Example User model using Sequelize
const { DataTypes, Model } = require('sequelize');
const sequelize = require('../utils/database');

class User extends Model {}

User.init({
  id: {
    type: DataTypes.INTEGER,
    autoIncrement: true,
    primaryKey: true
  },
  username: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true
  },
  password: {
    type: DataTypes.STRING,
    allowNull: false
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true
  },
  role: {
    type: DataTypes.STRING,
    allowNull: false,
    defaultValue: 'customer'
  },
  full_name: {
    type: DataTypes.STRING,
    allowNull: true
  },
  user_type: {
    type: DataTypes.STRING,
    allowNull: true
  },
  is_active: {
    type: DataTypes.BOOLEAN,
    allowNull: false,
    defaultValue: true
  },
  phone_number: {
    type: DataTypes.STRING,
    allowNull: true
  }
}, {
  sequelize,
  modelName: 'User',
  tableName: 'users',
  timestamps: true
});

module.exports = User;
