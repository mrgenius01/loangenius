// Database initialization and seeding script for Node.js backend

require('dotenv').config();
const readline = require('readline');
const { ensureDatabaseExists } = require('./utils/ensureDb');
const sequelize = require('./utils/database');
const { User, Loan, Transaction } = require('./models');
const { hashPassword } = require('./services/hashService');

async function initializeDatabase() {
  console.log('🚀 Database Initialization Script');
  console.log('='.repeat(50));
  try {
    // Ensure DB exists before connecting
    await ensureDatabaseExists();
    await sequelize.sync({ force: true });
    console.log('  ✓ All tables created');

    // Create admin user if not exists
    const adminExists = await User.count({ where: { role: 'admin' } });
    if (!adminExists) {
      console.log('  🔧 Creating default admin user...');
      const admin = await User.create({
        username: 'admin',
        email: 'admin@example.com',
        full_name: 'System Administrator',
        role: 'admin',
        user_type: 'admin',
        is_active: true,
        password: await hashPassword('admin123')
      });
      console.log('  ✓ Admin user created: admin/admin123');
    }

    // Create sample customers if not exists
    const customerExists = await User.count({ where: { role: 'customer' } });
    if (!customerExists) {
      console.log('  📋 Creating sample customer data...');
      const customers = [
        {
          username: 'john_doe',
          email: 'john@example.com',
          full_name: 'John Doe',
          phone_number: '0771234567',
          role: 'customer',
          user_type: 'customer',
          is_active: true,
          password: await hashPassword('password123')
        },
        {
          username: 'jane_smith',
          email: 'jane@example.com',
          full_name: 'Jane Smith',
          phone_number: '0779876543',
          role: 'customer',
          user_type: 'customer',
          is_active: true,
          password: await hashPassword('password123')
        },
        {
          username: 'mike_wilson',
          email: 'mike@example.com',
          full_name: 'Mike Wilson',
          phone_number: '0775555555',
          role: 'customer',
          user_type: 'customer',
          is_active: true,
          password: await hashPassword('password123')
        }
      ];
      const createdCustomers = await User.bulkCreate(customers);
      console.log('  ✓ Sample customers created');

      // Create sample loans
      const john = createdCustomers.find(u => u.username === 'john_doe');
      const jane = createdCustomers.find(u => u.username === 'jane_smith');
      const mike = createdCustomers.find(u => u.username === 'mike_wilson');
      const loans = [
        {
          userId: john.id,
          amount: 1000.00,
          status: 'active',
        },
        {
          userId: jane.id,
          amount: 500.00,
          status: 'active',
        },
        {
          userId: mike.id,
          amount: 2000.00,
          status: 'active',
        },
        {
          userId: john.id,
          amount: 300.00,
          status: 'completed',
        }
      ];
      const createdLoans = await Loan.bulkCreate(loans);
      console.log('  ✓ Sample loans created:', createdLoans.map(l => l.toJSON ? l.toJSON() : l));

      // Create sample transactions
      const transactions = [
        {
          userId: john.id,
          amount: 50.00,
          type: 'loan_payment',
          phone_number: john.phone_number,
          method: 'ecocash'
        },
        {
          userId: jane.id,
          amount: 50.00,
          type: 'loan_payment',
          phone_number: jane.phone_number,
          method: 'ecocash'
        }
      ];
      await Transaction.bulkCreate(transactions);
      console.log('  ✓ Sample transactions created');
    }

    // Print summary
    const userCount = await User.count();
    const loanCount = await Loan.count();
    const transactionCount = await Transaction.count();
    console.log('\n📊 Database Status:');
    console.log(`  👤 Users: ${userCount}`);
    console.log(`  🏦 Loans: ${loanCount}`);
    console.log(`  💰 Transactions: ${transactionCount}`);
    console.log('\n✅ Database initialization completed!');
    console.log('='.repeat(50));
    console.log('🎯 Your database is ready with:');
    console.log('  ✓ All necessary tables and relationships');
    console.log('  ✓ Sample data for testing');
    console.log('\n🔑 Login Credentials:');
    console.log('  Admin: admin / admin123');
    console.log('  Customer: john_doe / password123');
    console.log('  Customer: jane_smith / password123');
    console.log('  Customer: mike_wilson / password123');
    return true;
  } catch (e) {
    console.error('\n❌ Database initialization failed:', e);
    return false;
  }
}

if (require.main === module) {
  (async () => {
    const success = await initializeDatabase();
    if (success) {
      console.log('\n🎉 Database ready! You can now run your loan management system.');
      process.exit(0);
    } else {
      console.log('\n❌ Please check the errors above and try again.');
      process.exit(1);
    }
  })();
}
