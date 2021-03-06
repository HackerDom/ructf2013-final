package VAPI::App;
use Dancer ':syntax';
use DBI;
use JSON;
use strict;
no warnings;

our $VERSION = '0.1';
my $PRETTY = 0;         # Pretty JSON ?

my $dbh = session('dbh');

#######################################
prefix undef;
#######################################

get '/' => sub {
    header('Access-Control-Allow-Origin' => '*');
    return "Hello. Current time is: " . time;
};

get '/points_history' => sub {
    header('Access-Control-Allow-Origin' => '*');
    db_connect();
    my $time = int(params->{time});
    my $sql = "SELECT round,trunc(extract('epoch' from time)) AS time, team, trunc(rank) AS rank FROM ".
                "flag_price WHERE EXTRACT('epoch' from time) > $time ORDER BY time";
    my @result;
    my %teams = db_readhash('teams', 'id', 'name');
    my %data = map { $_ => [] } keys %teams;

    my $sth = $dbh->prepare($sql);
    $sth->execute();
    while(my $ref = $sth->fetchrow_hashref()) {
        # $result{ $ref->{$key} } = $ref->{$value};
        push @{$data{$ref->{team}}}, $ref->{rank};
    }
    for (sort keys %teams) {
        push @result, { 
            team   => $teams{$_},
            points => $data{$_}
        };
    }
    return JSON::to_json( \@result, { pretty => $PRETTY } );
};

get '/time_left' => sub {
    header('Access-Control-Allow-Origin' => '*');
    db_connect();
    my $sql = 
        "SELECT EXTRACT('epoch' FROM main) - EXTRACT('epoch' FROM NOW()) AS main, ".
        "LEAST(EXTRACT('epoch' FROM extra)-EXTRACT('epoch' FROM NOW()), EXTRACT('epoch' FROM extra)-EXTRACT('epoch' FROM main)) ".
        "AS extra FROM deadline LIMIT 1";

    my ($main,$extra) = (0,0);
    my $sth = $dbh->prepare($sql);
    $sth->execute();
    if (my $ref = $sth->fetchrow_hashref()) {
        $main  = int $ref->{main}  if $ref->{main}>=0;
        $extra = int $ref->{extra} if $ref->{extra}>=0;
    }
    return JSON::to_json( { main_time => $main, extra_time => $extra } );
};

#######################################

sub db_connect {
    return if defined $dbh;
    my $connstr = sprintf "DBI:Pg:dbname=%s;host=%s;port=%d", config->{db_name}, config->{db_host}, config->{db_port};
    $dbh = DBI->connect($connstr, config->{db_user}, config->{db_pass}, {'RaiseError' => 1});
    session 'dbh' => $dbh;
}

sub db_readhash {
    my ($table,$key,$value)=@_;
    my %result;
    my $sth = $dbh->prepare("SELECT $key, $value FROM $table");
    $sth->execute();
    while(my $ref = $sth->fetchrow_hashref()) {
            $result{ $ref->{$key} } = $ref->{$value};
    }
    return %result;
}

sub json {
    my %in = @_;
    return "{" . join(',', map {"\"$_\":\"$in{$_}\""} sort keys %in) . "}";
}
