// Add more models as needed, e.g., Loan, Transaction
// Example Transaction model
const { DataTypes, Model } = require('sequelize');
const sequelize = require('../utils/database');

class Transaction extends Model {}

Transaction.init({
  id: {
    type: DataTypes.INTEGER,
    autoIncrement: true,
    primaryKey: true
  },
  amount: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false
  },
  type: {
    type: DataTypes.STRING,
    allowNull: false
  },
  userId: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  phone_number: {
    type: DataTypes.STRING,
    allowNull: false
  },
  method: {
    type: DataTypes.STRING,
    allowNull: false
  },
  status: {
    type: DataTypes.STRING,
    allowNull: false,
    defaultValue: 'pending'
  },
  reference: {
    type: DataTypes.STRING,
    allowNull: true
  },
  pollUrl: {
    type: DataTypes.STRING,
    allowNull: true
  },
  instructions: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  error: {
    type: DataTypes.TEXT,
    allowNull: true
  }
}, {
  sequelize,
  modelName: 'Transaction',
  tableName: 'transactions',
  timestamps: true
});

module.exports = Transaction;
