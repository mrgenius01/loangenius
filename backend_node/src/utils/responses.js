// Centralized response helpers
function successResponse(res, data, message = 'Success') {
  return res.status(200).json({ message, data });
}

function errorResponse(res, error, status = 400) {
  return res.status(status).json({ error });
}

module.exports = { successResponse, errorResponse };
