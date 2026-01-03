# Contributing to EasyDispatch

Thank you for your interest in contributing to EasyDispatch! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

**Great Bug Reports Include:**
- Clear and descriptive title
- Exact steps to reproduce the problem
- Expected vs actual behavior
- Screenshots if applicable
- System information (Raspberry Pi model, OS version, MMDVM hat version)
- Relevant log files

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:
- Clear description of the enhancement
- Use case and benefits
- Possible implementation approach
- Examples from similar projects

### Pull Requests

1. **Fork the repository**
2. **Create a branch** (`git checkout -b feature/AmazingFeature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
6. **Push to the branch** (`git push origin feature/AmazingFeature`)
7. **Open a Pull Request**

## Development Setup

### Prerequisites

- Raspberry Pi 3 or newer (for hardware testing)
- MMDVM_HS_Dual_Hat
- Python 3.9+
- PHP 7.4+
- MySQL 5.7+ or MariaDB 10.2+

### Setting Up Development Environment

#### Raspberry Pi Side

```bash
# Clone repository
git clone https://github.com/cris-deitos/EasyDispatch.git
cd EasyDispatch

# Create virtual environment
cd raspberry/easydispatch-collector
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

#### Backend Side

```bash
# Set up database
mysql -u root -p < backend/database/schema.sql

# Configure web server (see INSTALLATION.md)
```

## Code Style

### Python

Follow PEP 8 style guide:

```python
# Good
def process_transmission(radio_id, data):
    """Process a DMR transmission."""
    if not data:
        return None
    return data.decode('utf-8')

# Use descriptive names
# Add docstrings
# Keep functions focused
```

### PHP

Follow PSR-12 coding standard:

```php
<?php
// Good
function processTransmission($radioId, $data) {
    if (!$data) {
        return null;
    }
    return json_decode($data, true);
}

// Use camelCase for variables
// Add type hints when possible
// Return early
```

### Shell Scripts

```bash
#!/bin/bash
# Use set -e for error handling
set -e

# Quote variables
echo "Processing file: ${FILENAME}"

# Check for errors
if [ ! -f "${FILENAME}" ]; then
    echo "Error: File not found"
    exit 1
fi
```

## Testing

### Python Tests

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=collector tests/
```

### PHP Tests

```bash
# Run PHPUnit (if implemented)
phpunit tests/

# Manual API testing
curl -H "Authorization: Bearer YOUR_KEY" \
     http://localhost/api/v1/radios
```

### Integration Testing

1. Start MMDVM services
2. Start collector
3. Transmit test message
4. Verify in database
5. Check audio file created
6. Test API endpoints

## Documentation

When adding features, update:
- Code comments
- Docstrings
- README.md (if significant feature)
- Relevant guide in `raspberry/docs/`
- CHANGELOG.md

## Commit Messages

Use clear, descriptive commit messages:

```
# Good
Add GPS accuracy validation
Fix audio capture memory leak
Update frequency configuration guide

# Bad
fix bug
update
changes
```

Format:
```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
```

## Pull Request Process

1. **Update documentation** for any user-facing changes
2. **Add tests** if adding new functionality
3. **Update CHANGELOG.md** with your changes
4. **Ensure all tests pass**
5. **Request review** from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests pass
```

## Project Structure

```
EasyDispatch/
├── raspberry/              # Raspberry Pi components
│   ├── easydispatch-collector/
│   │   ├── collector/     # Core modules - add new modules here
│   │   ├── config/        # Configuration templates
│   │   └── main.py        # Entry point
│   ├── scripts/           # Utility scripts
│   └── docs/              # Documentation
│
└── backend/               # Backend API
    ├── api/
    │   ├── v1/           # API endpoints - add new endpoints here
    │   ├── config/       # Configuration
    │   ├── middleware/   # Middleware
    │   └── utils/        # Utilities
    └── database/         # Database schemas
```

## Adding New Features

### Adding a New Collector Module

1. Create `raspberry/easydispatch-collector/collector/your_module.py`
2. Add to `__init__.py`
3. Import in `main.py`
4. Add configuration to `config.yaml.example`
5. Update documentation

### Adding a New API Endpoint

1. Create `backend/api/v1/your_endpoint.php`
2. Include necessary modules (cors, auth, etc.)
3. Implement GET/POST/etc. handlers
4. Add validation
5. Update database schema if needed
6. Document in README

### Adding a Database Table

1. Add to `backend/database/schema.sql`
2. Create migration in `backend/database/migrations/`
3. Update documentation
4. Add indexes for performance
5. Consider foreign keys

## Performance Considerations

- **Raspberry Pi**: Limited resources
  - Keep memory usage low
  - Avoid heavy processing
  - Use generators for large datasets
  
- **Backend**: May handle multiple Raspberry Pis
  - Optimize queries
  - Use indexes
  - Cache when appropriate
  - Consider rate limiting

## Security Guidelines

- **Never commit secrets** (API keys, passwords)
- **Validate all input**
- **Use prepared statements** for SQL
- **Sanitize file uploads**
- **Implement rate limiting**
- **Use HTTPS** in production
- **Keep dependencies updated**

## Getting Help

- **Documentation**: Check `raspberry/docs/`
- **Issues**: Search existing issues
- **Discussions**: Start a discussion for questions
- **Contact**: Reach out to maintainers

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in commit history

Thank you for contributing to EasyDispatch! 🎉
