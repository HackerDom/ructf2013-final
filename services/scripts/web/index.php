<?php 
  require_once 'inc/common.php';
  require_once 'inc/i18n.php';
  require_once 'inc/users.php';

  $params = check_args(array('session'));
  if (array_key_exists('session', $params) && is_logon($params['session']))
  {
    require 'create.php';
    exit;
  }

  i18n_template('index');
?>