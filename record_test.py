import unittest

from .record import *

class MutableRecordTest(unittest.TestCase):
	def test_required(self):
		Foo = make_mutable_type("Foo", a=Required)
		with self.assertRaises(DataError):
			f = Foo()
		f = Foo(a=123)
		self.assertEqual(f.a, 123)

	def test_instanceof(self):
		Foo = make_mutable_type("Foo", a=InstanceOf(dict))
		with self.assertRaises(DataError):
			f = Foo(a=1)
		with self.assertRaises(DataError):
			f = Foo(a=None)
		with self.assertRaises(DataError):
			f = Foo()
		f = Foo(a={})
		self.assertEqual(f.a, {})

	def test_instanceornone(self):
		Foo = make_mutable_type("Foo", a=InstanceOrNone(dict))
		with self.assertRaises(DataError):
			f = Foo(a=1)
		f = Foo(a=None)
		self.assertEqual(f.a, None)
		f = Foo(a={})
		self.assertEqual(f.a, {})
		f = Foo()
		self.assertEqual(f.a, None)

	def test_oneof(self):
		Foo = make_mutable_type("Foo", a=OneOf("a", "b", "c"))
		with self.assertRaises(DataError):
			f = Foo(a="d")
		with self.assertRaises(DataError):
			f = Foo(a=None)
		with self.assertRaises(DataError):
			f = Foo()
		f = Foo(a="a")
		self.assertEqual(f.a, "a")

	def test_oneof_with_default(self):
		Foo = make_mutable_type("Foo", a=OneOf("a", "b", "c", default="c"))
		with self.assertRaises(DataError):
			f = Foo(a="d")
		f = Foo()
		self.assertEqual(f.a, "c")
		f = Foo(a="a")
		self.assertEqual(f.a, "a")

	def test_length(self):
		Foo = make_mutable_type("Foo", a=Length(3))
		with self.assertRaises(DataError):
			f = Foo()
		with self.assertRaises(DataError):
			f = Foo(a=1)
		with self.assertRaises(DataError):
			f = Foo(a=[1, 2])
		f = Foo(a=[1, 2, 3])
		self.assertEqual(f.a, [1, 2, 3])

	def test_simple_record(self):
		Foo = make_mutable_type("Foo", a=1, b=2)
		f1 = Foo(a=123)
		self.assertEqual(f1.a, 123)
		self.assertEqual(f1.b, 2)

	def test_complex_record(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam"))
		f = Foo(a=1, c="ham")
		self.assertEqual(f.a, 1)
		self.assertEqual(f.b, 2)
		self.assertEqual(f.c, "ham")


class MutableRecordSetTest(unittest.TestCase):
	def test_construct_empty(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		self.assertEqual(len(fs), 0)

	def test_construct_from_list(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List([Foo(a=1), Foo(a=2)])
		self.assertEqual(len(fs), 2)
		self.assertEqual(fs[0].a, 1)
		self.assertEqual(fs[1].a, 2)

	def test_getitem(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		fs.append_new(a=1, c="ham")
		fs.append_new(a=2, c="ham")
		fs.append_new(a=3, c="ham")
		x = fs[1]
		self.assertIsInstance(x, Foo)
		self.assertEqual(x.a, 2)

	def test_setitem(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		fs.append_new(a=1, c="ham")
		fs.append_new(a=2, c="ham")
		fs.append_new(a=3, c="ham")
		fs[1] = Foo(a=100, c="spam")
		self.assertEqual(fs[1].a, 100)
		self.assertEqual(fs[1].b, 2)
		self.assertEqual(fs[1].c, "spam")

	def test_mutate_item(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		fs.append_new(a=1, c="ham")
		fs.append_new(a=2, c="ham")
		fs.append_new(a=3, c="ham")
		fs[1].a = 100
		self.assertEqual(fs[1].a, 100)

	def test_getslice(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		fs.append_new(a=1, c="ham")
		fs.append_new(a=2, c="ham")
		fs.append_new(a=3, c="ham")
		x = fs[1:]
		self.assertIsInstance(x, Foo.List)
		self.assertEqual(len(x), 2)
		self.assertEqual(x[0].a, 2)
		self.assertEqual(x[1].a, 3)

	def test_setslice(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		fs.append_new(a=1, c="ham")
		fs.append_new(a=2, c="ham")
		fs.append_new(a=3, c="ham")
		fs[:2] = [Foo(a=10, c="spam")]
		self.assertEqual(len(fs), 2)
		self.assertEqual(fs[0].a, 10)
		self.assertEqual(fs[1].a, 3)

	def test_append(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List([Foo(a=1)])
		fs.append(Foo(a=2))
		self.assertEqual(len(fs), 2)
		self.assertEqual(fs[0].a, 1)
		self.assertEqual(fs[1].a, 2)

	def test_append_new(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List()
		fs.append_new(a=1, c="ham")
		self.assertEqual(len(fs), 1)
		self.assertEqual(fs[0].a, 1)
		self.assertEqual(fs[0].b, 2)
		self.assertEqual(fs[0].c, "ham")

	def test_insert(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List([Foo(a=1)])
		fs.insert(0, Foo(a=2))
		self.assertEqual(len(fs), 2)
		self.assertEqual(fs[0].a, 2)
		self.assertEqual(fs[1].a, 1)

	def test_insert_new(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List([Foo(a=1)])
		fs.insert_new(0, a=2)
		self.assertEqual(len(fs), 2)
		self.assertEqual(fs[0].a, 2)
		self.assertEqual(fs[1].a, 1)

	def test_extend(self):
		Foo = make_mutable_type("Foo", a=Required, b=2, c=OneOf("ham", "spam", default="ham"))
		fs = Foo.List([Foo(a=1)])
		fs.extend([Foo(a=2), Foo(a=3)])
		self.assertEqual(len(fs), 3)
		self.assertEqual(fs[0].a, 1)
		self.assertEqual(fs[1].a, 2)
		self.assertEqual(fs[2].a, 3)

class FieldViewTest(unittest.TestCase):
	def test_getitem(self):
		Foo = make_mutable_type("Foo", x=Required)
		fs = Foo.List([Foo(x=1), Foo(x=2), Foo(x=3)])
		xs = fs.xs
		self.assertEqual(len(xs), 3)
		self.assertEqual(xs[0], 1)
		self.assertEqual(xs[1], 2)
		self.assertEqual(xs[2], 3)

	def test_setitem(self):
		Foo = make_mutable_type("Foo", x=Required)
		fs = Foo.List([Foo(x=1), Foo(x=2), Foo(x=3)])
		xs = fs.xs
		xs[1] = 100
		self.assertEqual(fs[1].x, 100)

	def test_getslice(self):
		Foo = make_mutable_type("Foo", x=Required)
		fs = Foo.List([Foo(x=1), Foo(x=2), Foo(x=3)])
		xs = fs.xs[1:]
		self.assertEqual(len(xs), 2)
		self.assertEqual(xs[0], 2)
		self.assertEqual(xs[1], 3)

	def test_setslice(self):
		Foo = make_mutable_type("Foo", x=Required)
		fs = Foo.List([Foo(x=1), Foo(x=2), Foo(x=3)])
		fs.xs[1:] = [100, 200]
		self.assertEqual(fs[0].x, 1)
		self.assertEqual(fs[1].x, 100)
		self.assertEqual(fs[2].x, 200)

	def test_iter(self):
		Foo = make_mutable_type("Foo", x=Required)
		fs = Foo.List([Foo(x=1), Foo(x=2), Foo(x=3)])
		self.assertListEqual(list(iter(fs.xs)), [1, 2, 3])


class MetaclassTest(unittest.TestCase):
	def test_simple_record(self):
		class Foo(object, metaclass=MutableRecordType):
			a = 1
			b = 2

		f1 = Foo(a=123)
		self.assertEqual(f1.a, 123)
		self.assertEqual(f1.b, 2)

	def test_complex_record(self):
		class Foo(object, metaclass=MutableRecordType):
			a = Required
			b = 2
			c = OneOf("ham", "spam")

		f = Foo(a=1, c="ham")
		self.assertEqual(f.a, 1)
		self.assertEqual(f.b, 2)
		self.assertEqual(f.c, "ham")

	def test_required(self):
		class Foo(object, metaclass=MutableRecordType):
			a = Required

		with self.assertRaises(DataError):
			f = Foo()
		f = Foo(a=123)
		self.assertEqual(f.a, 123)

	def test_member_func(self):
		class Foo(object, metaclass=MutableRecordType):
			a = Required
			def bar(self):
				return self.a + 1

		f = Foo(a=1)
		self.assertEqual(f.bar(), 2)


if __name__ == '__main__':
	unittest.main()
