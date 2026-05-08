import { ButtonGroup, Button } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import React from 'react';
import PropTypes from 'prop-types'

const routes = {
  math: '/query',
  english: '/english',
};

const palette = {
  default: '#f4881c',
  hover: '#e07617',
  selected: '#d66814',
  selectedHover: '#c45e12',
};

const getButtonStyles = (isSelected) => ({
  backgroundColor: isSelected ? palette.selected : palette.default,
  '&:hover': {
    backgroundColor: isSelected ? palette.selectedHover : palette.hover,
  },
  color: '#fff',
  textTransform: 'none',
});

export default function SubjectToggle(props) {
  const { className } = props;
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;

  const isMathSelected = currentPath === routes.math;
  const isEnglishSelected = currentPath === routes.english;

  const handleNavigate = (path) => {
    if (currentPath !== path) {
      navigate(path);
    }
  };

  return (
    <ButtonGroup
      disableElevation
      className={className}
      sx={{
        '& .MuiButton-root': {
          borderColor: 'transparent',
        },
      }}
    >
      <Button
        onClick={() => handleNavigate(routes.math)}
        sx={getButtonStyles(isMathSelected)}
      >
        Math
      </Button>
      <Button
        onClick={() => handleNavigate(routes.english)}
        sx={getButtonStyles(isEnglishSelected)}
      >
        English
      </Button>
    </ButtonGroup>
  );
}

SubjectToggle.propTypes = {
  className: PropTypes.string,
};

