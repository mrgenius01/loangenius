// Centralized error handler middleware
function errorHandler(err, req, res, next) {
  // Log error details for diagnostics
  console.error(err);

  // Customize error response
  const status = err.status || 500;
  const message = err.message || 'Internal Server Error';
  const details = process.env.NODE_ENV === 'production' ? undefined : err.stack;

  res.status(status).json({
    error: {
      message,
      ...(details && { details })
    }
  });
}

module.exports = { errorHandler };
