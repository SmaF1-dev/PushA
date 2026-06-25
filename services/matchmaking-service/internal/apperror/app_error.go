package apperror

// Type represents a high-level category of application error.
// HTTP handlers use it to map business errors to proper HTTP status codes.
type Type string

const (
	TypeValidation Type = "VALIDATION"
	TypeConflict   Type = "CONFLICT"
	TypeNotFound   Type = "NOT_FOUND"
	TypeInternal   Type = "INTERNAL"
)

// AppError is a typed business error returned by service layer methods.
//
// It contains a stable error code for API clients and an optional field name for
// validation errors.
type AppError struct {
	Type    Type
	Code    string
	Message string
	Field   string
}

func (e *AppError) Error() string {
	return e.Message
}

func NewValidation(code string, message string, field string) *AppError {
	return &AppError{
		Type:    TypeValidation,
		Code:    code,
		Message: message,
		Field:   field,
	}
}

func NewConflict(code string, message string) *AppError {
	return &AppError{
		Type:    TypeConflict,
		Code:    code,
		Message: message,
	}
}

func NewNotFound(code string, message string) *AppError {
	return &AppError{
		Type:    TypeNotFound,
		Code:    code,
		Message: message,
	}
}

func NewInternal(code string, message string) *AppError {
	return &AppError{
		Type:    TypeInternal,
		Code:    code,
		Message: message,
	}
}
