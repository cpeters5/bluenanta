#!/usr/bin/perl
#use 5.010;
#----------------
#  This script updates num species, hybrids, and image counts in Genus table
#------
##############################
use warnings FATAL => 'all';
use strict;
use Dotenv;
use DBI;
use Time::Duration;
use POSIX qw(strftime);
Dotenv->load("/webapps/bluenanta/.env");

my $HOST = '134.209.46.210';
my $DB = $ENV{'DBNAME'};
my $dbh = DBI->connect( "DBI:MariaDB:$DB:$ENV{'DBHOST'}","chariya",$ENV{'MYDBPSSWD'}) or die( "Could not connect to: $DBI::errstr" );
my ($sth, $sth1);
&getASPM("use $DB");

# use open qw(:locale);

my @apps = (
	# 'orchidaceae',
	'other',
	'fungi',
	'aves',
	'animalia'
);
my $date = strftime "%Y-%m-%d:%H:%M-%S", localtime;
# our ($DB,$stf,$sth, $rc, $sth1, $sth2, $dbh);
# my $datestring = strftime "%a %b %e %H:%M:%S %Y", localtime();
my $datetime = localtime();
my $start_time = time();
my $debug = 1;
my ($stmt,%num_image,%num_species, %num_hybrid, %num_hybimage, %num_spcimage,
	%num_hyb_with_image,%num_spc_with_image,@accepted, %synonym,
	%num_species_synonym,%num_hybrid_synonym,%num_synonym, %genus,
	%num_species_total, %num_hybrid_total,%num_image_gen,
	%num_famhybimage, %num_famspcimage,
 );


foreach my $app (@apps) {
	# print "$app - Initialize PID\n" if $debug;
	getPID($app);

	# print "$app - Count hybimages and spcimages\n" if $debug;
	getSpcImages($app);
	getHybImages($app) if $app eq 'orchidaceae';

	# print "$app - get synonym pid\n" if $debug;
	getSynonymPid($app);

	# print "$app - Processing genus\n" if $debug;
	procGenus($app);

	# print "$app - Processing species\n" if $debug;
	procSpecies($app);

	# Synonyms now have its own detailed view
	# print "$app - process synonym pid\n" if $debug;
	# processSynonym($app);
}
print "Process Family\n" if $debug;
getFamImage();
print "$date\t Runtime = ", duration(time() - $start_time), "\n";

sub getFamImage {
	my $stmt = "select sum(num_spcimage), family from other_genus group by 2 order by 2";
	# Both species and hybrid images are in the same table
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		$num_famspcimage{$row[1]} = $row[0] if $row[0] and $row[0] > 0;
	}
	$stmt = "select sum(num_spcimage), sum(num_hybimage), family from orchidaceae_genus group by 3 order by 3";
	&getASPM($stmt);
	while (my @row = $sth->fetchrow_array()) {
		$num_famhybimage{$row[2]} = $row[1] if $row[1] and $row[1] > 0;
		$num_famspcimage{$row[2]} = $row[0] if $row[0] and $row[0] > 0;
	}


	# foreach (sort keys %num_famspcimage) {
	# 	# print "$_\t$num_famspcimage{$_}\n";
	# 	$stmt = "update common_family set num_spcimage = $num_famspcimage{$_} where family = '$_';";
	# 	# print "$stmt\n";
	# 	&getASPM($stmt);
	# }
	# foreach (sort keys %num_famhybimage) {
	# 	$stmt = "update common_family set num_hybimage = $num_famhybimage{$_} where family = '$_';";
	# 	# print "$stmt\n";
	# 	&getASPM($stmt);
	#
	# }
}


sub procGenus {
	my $app = shift;
	my $i = 0;
	# &getASPM("UPDATE bluenanta_genus set num_species = 0, num_hybrid = 0, num_species_synonym=0, num_species_total=0,
	# 			num_spc_with_image=0,pct_spc_with_image=0,num_hybrid=0,num_hybrid_synonym=0,num_hybrid_total=0,
	# 			num_hyb_with_image=0,pct_hyb_with_image=0");

    # First, set all statistic fields to empty
    &getASPM("UPDATE " . $app . "_genus
	            set num_species = NULL,
	            num_species_synonym = NULL,
	            num_spcimage = NULL,
	            num_species_total = NULL,
	            num_spc_with_image = NULL,
	            num_hybrid = NULL,
	            num_hybrid_synonym = NULL,
	            num_hybimage = NULL,
	            num_hybrid_total = NULL,
	            num_hyb_with_image = NULL");
	foreach my $pid (sort keys %genus) {
		next if not $num_spcimage{$pid} and not $num_species_synonym{$pid} and not $num_species{$pid};
        $stmt = "update " . $app . "_genus set ";
		$stmt .= "num_species = $num_species{$pid}, " if $num_species{$pid};
		$stmt .= "num_species_synonym = $num_species_synonym{$pid}, " if $num_species_synonym{$pid};
		$stmt .= "num_spcimage = $num_spcimage{$pid}, " if $num_spcimage{$pid};

		my $total = $num_species{$pid} + $num_species_synonym{$pid};
		$stmt .= "num_species_total = $total, " if $total;
		if ($num_spc_with_image{$pid}) {
            my $pct = 0;
			$pct = sprintf("%.1f",$num_spc_with_image{$pid}*100/$num_species{$pid}) if $num_species{$pid} > 0;
            $stmt .= "num_spc_with_image = $num_spc_with_image{$pid}, pct_spc_with_image = $pct, ";
        }
		$stmt .= "num_hybrid = $num_hybrid{$pid}, " if $num_hybrid{$pid};
		$stmt .= "num_hybrid_synonym = $num_hybrid_synonym{$pid}, " if $num_hybrid_synonym{$pid};
		$stmt .= "num_hybimage = $num_hybimage{$pid}, " if $num_hybimage{$pid};
		$total = $num_hybrid{$pid} + $num_hybrid_total{$pid};
		$stmt .= "num_hybrid_total = $total, " if $total;
        if ($num_hyb_with_image{$pid}) {
			my $pct = 0;
            $pct = sprintf("%.1f", $num_hyb_with_image{$pid} * 100 / $num_hybrid{$pid}) if $num_hybrid{$pid};
            $stmt .= "num_hyb_with_image = $num_hyb_with_image{$pid}, pct_hyb_with_image = $pct, ";
        }
		$stmt =~ s/, $//;
		$stmt .= " where pid = $pid";
		# print "$stmt\n" if $num_spcimage{$pid};
		&getASPM($stmt);
	}
}


sub procSpecies {
	my $app = shift;
	my $i = 0;
	&getASPM("UPDATE " . $app . "_species set num_image = 0");
	foreach my $pid (sort keys %num_image) {
		next if $num_image{$pid} == 0;
        $stmt = "update " . $app . "_species set num_image = $num_image{$pid} where pid = $pid";
		&getASPM($stmt);
	}
}


sub processSynonym {
	# Set num image for each synonym = num inage of its accepted species
	my $app = shift;
	my $i = 0;

	foreach (sort keys %synonym) {
		$stmt = "update " . $app . "_species set num_image = $synonym{$_} where pid = $_;";
print "pid = $_\n $stmt\n" if $_ == 300000910282;
		&getASPM($stmt);
	}
}


sub getPID {
	my $app = shift;
	$stmt = "select pid, type, gen, status from " . $app . "_species where pid > 0 and type is not null and gen is not null order by 3;";
	print "$stmt\n" if $debug;
	&getASPM($stmt);
	my $prevgen = 0;
    my %seen;
	while (my @row = $sth->fetchrow_array()) {
		$seen{$row[2]}++;
        if ($row[2] != $prevgen) {
			# Initialize all counts
            $genus{$row[2]} = 0;
			$num_species{$row[2]} = 0;
			$num_species_synonym{$row[2]} = 0;
			$num_hybrid{$row[2]} = 0;
			$num_hybrid_synonym{$row[2]} = 0;
			$num_image_gen{$row[2]} = 0;
		}
        $num_image{$row[0]} = 0;
		$genus{$row[2]}++;
		if ($row[1] eq 'species') {
			if ($row[3] eq 'synonym') {
				$num_species_synonym{$row[2]}++;
			}
			else {
				$num_species{$row[2]}++;
			}
		}
		elsif ($row[1] eq 'hybrid') {
			if ($row[3] eq 'synonym') {
				$num_hybrid_synonym{$row[2]}++;
			}
			else {
				$num_hybrid{$row[2]}++;
			}
		}
        else {
            print "What type is this: pid $row[0]\ttype: $row[1]\tgen: $row[2]\n";
        }
		$prevgen = $row[2];
	}

	foreach (sort keys %genus) {
		$num_species{$_} = 0 if not $num_species{$_};
		$num_species_synonym{$_} = 0 if not $num_species_synonym{$_};
		$num_hybrid{$_} = 0 if not $num_hybrid{$_};
		$num_hybrid_synonym{$_} = 0 if not $num_hybrid_synonym{$_};
		$num_synonym{$_} = $genus{$_} - $num_species{$_} - $num_hybrid{$_};
		$num_species_total{$_} = $num_species{$_} + $num_species_synonym{$_};
		$num_hybrid_total{$_} = $num_hybrid{$_} + $num_hybrid_synonym{$_};
	}

}


sub getSynonymPid {
	# Set num image for synonym to be the same as its accepted species
	my $app = shift;
	foreach (keys %num_image) {
		$stmt = "select spid, acc_id from " . $app . "_synonym where acc_id = $_ ";
		&getASPM($stmt);
		while (my @row = $sth->fetchrow_array()) {
			# next if $num_image{$_} == 0;
			$synonym{$row[0]} = $num_image{$row[0]};
		}
	}
}

sub getHybImages {
	my $app = shift;
	cleanup();
	# Initialize num images
	$stmt = "select count(*) c, pid, gen from " . $app . "_hybimages where `rank` > 0 and pid < 999999999 group by 2, 3 order by 3;";
	&getASPM($stmt);
	my $prevgen = 0;
	while (my @row = $sth->fetchrow_array()) {
		if ($row[2] != $prevgen) {
			$num_image_gen{$row[2]} = 0;
			$num_hyb_with_image{$row[2]} = 0;
			$num_hybimage{$row[2]} = 0;
			$prevgen = $row[2];
		}
		next if $row[0] == 0;
		$num_image{$row[1]} = $row[0] if $row[1] and $row[0];
		# Data for genus stat
		$num_image_gen{$row[2]} += $row[0];
		$num_hyb_with_image{$row[2]}++;
		$num_hybimage{$row[2]} += $row[0];
	}
}

sub getSpcImages {
	my $app = shift;
	cleanup();
	$stmt = "select count(*) c, pid, gen from " . $app . "_spcimages where `rank` > 0 group by 2, 3 order by 3;";
	print "$stmt\n" if $debug;
	&getASPM($stmt);
	my $prevgen = 0;
	while (my @row = $sth->fetchrow_array()) {
		next if not $row[1];
		if ($row[2] != $prevgen and $prevgen != 0) {
			$num_image_gen{$row[2]} = 0;
			$num_spc_with_image{$row[2]} = 0;
			$num_spcimage{$row[2]} = 0;
			$prevgen = $row[2];
		}
		next if $row[0] == 0;
		$num_image{$row[1]} = $row[0];
		$num_image_gen{$row[2]} += $row[0];
		$num_spc_with_image{$row[2]}++;
		$num_spcimage{$row[2]} += $row[0];
	}
}

sub getASPM {
	my $stmt = shift;
	$sth = $dbh->prepare( $stmt ) or die( "\n$stmt\nCannot prepare: ", $dbh->errstr(), "\n" );
	my $rc = $sth->execute() or die("\nDead! \n$stmt\nCannot execute: ", $sth->errstr(),"\n" );
}

sub cleanup() {
	foreach (keys  %num_image) {$num_image{$_} = 0;}
	foreach (keys  %num_species) {$num_species{$_} = 0;}
	foreach (keys  %num_hybrid) {$num_hybrid{$_} = 0;}
	foreach (keys  %num_hybimage) {$num_hybimage{$_} = 0;}
	foreach (keys  %num_spcimage) {$num_spcimage{$_} = 0;}
	foreach (keys  %num_hyb_with_image) {$num_hyb_with_image{$_} = 0;}
	foreach (keys  %num_spc_with_image) {$num_spc_with_image{$_} = 0;}
}
