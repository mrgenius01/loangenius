// Add more models as needed, e.g., Loan
const { DataTypes, Model } = require('sequelize');
const sequelize = require('../utils/database');

class Loan extends Model {}

Loan.init({
  id: {
    type: DataTypes.INTEGER,
    autoIncrement: true,
    primaryKey: true
  },
  amount: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: false
  },
  userId: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  status: {
    type: DataTypes.STRING,
    allowNull: false
  }
}, {
  sequelize,
  modelName: 'Loan',
  tableName: 'loans',
  timestamps: true
});

module.exports = Loan;
