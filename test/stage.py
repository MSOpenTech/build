#!/usr/bin/python

# Test staging

from BoostBuild import Tester
t = Tester()

t.write("project-root.jam", "import gcc ;")

t.write(
    "Jamfile", 
"""
lib a : a.cpp ;
stage dist : a a.h auxilliary/1 ;
""")

t.write(
    "a.cpp",
"""
int
#ifdef _WIN32
__declspec(dllexport)
#endif
must_export_something;
""")

t.write("a.h", "")
t.write("auxilliary/1", "")

t.run_build_system()
t.expect_addition(["dist/a.dll", "dist/a.h", "dist/1"])


# Regression test: the following was causing the "duplicate target name"
# error.
t.write(
    "Jamfile", 
"""
project : requirements <hardcode-dll-paths>true ;
lib a : a.cpp ;
stage dist : a a.h auxilliary/1 ;
alias dist-alias : dist ;
""")
t.run_build_system()


# Test the <location> property
t.write("Jamfile", """
lib a : a.cpp ;
stage dist : a 
    : <variant>debug:<location>ds <variant>release:<location>rs
    ;
""")

t.run_build_system()
t.expect_addition("ds/a.dll")

t.run_build_system("release")
t.expect_addition("rs/a.dll")

# Test the <location> property in subprojects. 
# Thanks to Kirill Lapshin for bug report.

t.write("project-root.jam", """
path-constant DIST : dist ;
""")

t.write("Jamfile", "build-project d ;")

t.write(
    "d/Jamfile",
"""
exe a : a.cpp ;
stage dist : a : <location>$(DIST) ;
""")

t.write("d/a.cpp", "int main() { return 0;}\n")

t.run_build_system()
t.expect_addition("dist/a.exe")

t.rm("dist")
# Workaround a BIG BUG: the response file is not deleted,
# even if application *is* deleted. We'll try to use the
# same response file when building from subdir, with very
# bad results.
t.rm("d/bin")
t.run_build_system(subdir="d")
t.expect_addition("dist/a.exe")


# Check that 'stage' does not incorrectly reset target suffixes.
t.write("a.cpp", """ 
int main() {} 
""")

t.write("project-root.jam", """ 
import type ;
type.register MYEXE : : EXE ;
type.set-generated-target-suffix MYEXE : <optimization>off : myexe ; 
""")

# Since <optimization>off is in properties when 'a' is built, and staged,
# it's suffix should be "myexe".
t.write("Jamfile", """ 
stage dist : a ;
myexe a : a.cpp ; 
""")

t.run_build_system()
t.expect_addition("dist/a.myexe")

# Test 'stage's ability to traverse dependencies.
t.write("a.cpp", """ 
int main() { return 0; }

""")

t.write("l.cpp", """
void
#if defined(_WIN32)
__declspec(dllexport)
#endif
foo() { }

""")

t.write("Jamfile", """ 
lib l : l.cpp ;
exe a : a.cpp l ;
stage dist : a : <traverse-dependencies>on <include-type>EXE <include-type>LIB ; 
""")

t.write("project-root.jam", "")

t.rm("dist")
t.run_build_system()
t.expect_addition("dist/a.exe")
t.expect_addition("dist/l.dll")

# Check that <use> properties are ignored the traversing
# target for staging.
t.copy("l.cpp", "l2.cpp")
t.copy("l.cpp", "l3.cpp")
t.write("Jamfile", """
lib l2 : l2.cpp ;
lib l3 : l3.cpp ;
lib l : l.cpp : <use>l2 <dependency>l3 ;
exe a : a.cpp l ;
stage dist : a : <traverse-dependencies>on <include-type>EXE <include-type>LIB ; 
""")

t.rm("dist")
t.run_build_system()
t.expect_addition("dist/l3.dll")
t.expect_nothing("dist/l2.dll")

# Check if <dependency> on 'stage' works.
t.rm(".")
t.write("Jamroot", """
stage a1 : a1.txt : <location>dist ;
stage a2 : a2.txt : <location>dist <dependency>a1 ;
""")
t.write("a1.txt", "")
t.write("a2.txt", "")
t.run_build_system("a2")
t.expect_addition(["dist/a1.txt", "dist/a2.txt"])

# Regression test: check if <location>. works
t.rm(".")
t.write("Jamroot", """
stage a1 : d/a1.txt : <location>. ;
""")
t.write("d/a1.txt", "")
t.run_build_system()
t.expect_addition("a1.txt")



t.cleanup()

